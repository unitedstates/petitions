#!/usr/bin/env python
import oauth2 as oauth    
import argparse
import os
import re
import json
import urllib
from urlparse import urlparse
from petitions import crawl
from utils import log, download, write, log_dir
from datetime import datetime

'''
search twitter for petitions, using the RESTful search API: https://dev.twitter.com/docs/api/1.1/get/search/tweets
it's not necessary to authenticate these calls, but doing so may grant higher rate limits
to authenticate, register a Twitter app to get OAuth keys: https://dev.twitter.com/apps/new
then put the keys and access tokens in keys.json, currently provided in the repo with blank values
'''

scrapelog = {
    "begin" : datetime.now().strftime("%Y-%m-%d-%H:%M:%S"),
    "signatures": {}
}

def search(query, start=1, mx=None): 
    if mx is None:
        mx = 1000
    
    hits = 0
    try:
        keys = json.load(open(os.getcwd() + '/scripts/keys.json', 'r'))
    except:
        keys = {
            "CONSUMER_KEY": "",
            "CONSUMER_SECRET": "",
            "ACCESS_TOKEN": "",
            "ACCESS_TOKEN_SECRET": ""
        }        
        
    # Create your consumer with the proper key/secret.
    consumer = oauth.Consumer(key=keys["CONSUMER_KEY"], secret=keys["CONSUMER_SECRET"])
    token = oauth.Token(keys["ACCESS_TOKEN"],keys["ACCESS_TOKEN_SECRET"])
    
    #list of urls we've visited to prevent duplicate calls, since RTs lead to many duplicate hits
    visited = []
    
    # Create our client.
    client = oauth.Client(consumer, token)    
 
    for pg in range(start, start + mx):
        url="http://search.twitter.com/search.json?page=%d&q=%s&rpp=100&include_entities=true&result_type=mixed" % (pg, query.replace(" ", "%20"))
        resp, content = client.request(url)
        results = json.loads(content)    
        if 'results' not in results:
            break
        
        for result in results['results']:
            for twurl in result['entities']['urls']:
                #see if this looks familiar
                if twurl['expanded_url'] in visited or twurl['url'] in visited:
                    continue            
                visited.append(twurl['expanded_url'])
                visited.append(twurl['url'])
    
                #check if it's a WH petitions
                parsed = urlparse(twurl['expanded_url'])
                petition_path = None
                #Looking for urls like this: http://petitions.whitehouse.gov/petition/propose-legislation-enacting-term-limits-congress/t5zpGgBV
                if parsed.netloc == "petitions.whitehouse.gov" and parsed.path.split("/")[1] == "petition":
                    petition_path = parsed.path
                elif len(twurl['expanded_url']) < 30: #crude heuristic for detecting possible shortened URL
                    #follow the url to see if it leads to something useful
                    try:
                        resp = urllib.urlopen(twurl['expanded_url'])
                    except:
                        log("error retrieving %s" % twurl['expanded_url'])
                        continue
                    parsed = urlparse(resp.url)
                    if parsed.netloc == "petitions.whitehouse.gov" and parsed.path.split("/")[1] == "petition":
                        petition_path = parsed.path
                if petition_path:
                    data = crawl(petition_path)
                    if data["status"] == "expired":
                        scrapelog["signatures"][petition_path.split("/")[2]] = -1
                    elif data["status"] == "active" or data["status"] == "answered":
                        scrapelog["signatures"][petition_path.split("/")[2]] = data["signatures"]
                        write(json.dumps(data, indent=2, sort_keys=True), petition_path.split("/")[2] + ".json")
                        
 
    #write log
    scrapelog["end"] = datetime.now().strftime("%Y-%m-%d-%H:%M:%S")
    write(json.dumps(scrapelog, indent=2), "log-twitter-" + scrapelog["begin"] + ".json", log_dir())

def main():
    parser = argparse.ArgumentParser(description="Retrieve petitions from We The People")
    parser.add_argument("-m", "--max", metavar="INTEGER", dest="max", type=int, default=None,
                        help="maximum pages of petitions to retrieve, default is 10, 100 per page")
    parser.add_argument("-s", "--start", metavar="INTEGER", dest="start", type=int, default=1,
                        help="starting page, 100 per page, default is 1")
    parser.add_argument("-q", "--query", metavar="STRING", dest="query", type=str, default="whitehouse+petition",
                        help="The query for searching twitter for petition links, default is 'whitehouse+petition'")
    args = parser.parse_args()

    if args.max is not None and args.max < 1:
        parser.error("How can I scrape less than one pages of twitter results? You make no sense! --max must be one or greater.")

    if args.start < 1:
        parser.error("--start must be one or greater.")

    search(args.query, args.start, args.max)

    #write log
    scrapelog["query"] = args.query    
    scrapelog["end"] = datetime.now().strftime("%Y-%m-%d-%H:%M:%S")
    write(json.dumps(scrapelog, indent=2), "log-tw-" + scrapelog["begin"] + ".json", log_dir())
    log("Found %i petitions" % (len(scrapelog["signatures"])))

if __name__ == "__main__":
    main()
