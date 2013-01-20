#!/usr/bin/env python
from StringIO import StringIO
import argparse
import json
from datetime import datetime
import scrapelib

from lxml.html import etree
from utils import log, download, write, log_dir


#intialize scraper and parser
s = scrapelib.Scraper(requests_per_minute=60, follow_robots=False)
parser = etree.HTMLParser()

scrapelog = {
    "begin" : datetime.now().strftime("%Y-%m-%d-%H:%M:%S"),
    "end": None,
    "signatures": {}
}

def petitions(mx=None, start=1):
    if mx is None:
        mx = -1
    
    #log objects for tracking signatures over time
    hits = 0
    
    #scan WH site, add any new petitions to DB
    #surely a better way to get indefinite number of results than to create a functionally infinite loop, then breaking it, but drawing a blank
    for pg in range(start, 1000):
        log("Loading page %d" % pg)

        #The WH site loads petitions from an external HTML doc in a JSON shell
        url = "https://petitions.whitehouse.gov/petitions/more/all/%d/2/0/" % pg
        try:
            raw = s.urlopen(url).encode('utf-8')
        except scrapelib.HTTPError:
            log("Error downloading %s" % url)
            return hits
        resp = json.loads(raw)
        if "markup" not in resp or len(resp["markup"]) == 0:
            log("No results at page %i" % pg)
            return hits
        page = etree.parse(StringIO(resp['markup']), parser)
        #there are two links to each petition in the results, but can reduce to uniques with "nofollow"

        for petition in page.xpath("body/div[@class]"):
            pid = petition.xpath("@id")[0].split('-')[1]
            #get uid for each petition from main div id
            path = petition.xpath("div/div/a/@href")[0]
            data = crawl(path, pid)
            #if petition is dead:
            if "created" not in data:
                scrapelog["signatures"][path.split("/")[2]] = -1
                continue            
            scrapelog["signatures"][path.split("/")[2]] = data["signatures"]
            write(json.dumps(data, indent=2, sort_keys=True), path.split("/")[2] + ".json")
            
            hits += 1
            if mx != -1 and hits >= mx:
                return hits


#visit the page for each petition and get the vitals
def crawl(path, pid=None):
    body = download("http://petitions.whitehouse.gov" + path, path.split('/')[2] + ".html")
    page = etree.parse(StringIO(body), parser)
    raw_date = page.xpath("//div[@class='date']/text()")[0].strip()
    created = datetime.strptime(raw_date, "%b %d, %Y").strftime("%Y-%m-%d")
    signatures = page.xpath("//div[@class='num-block num-block2']/text()")
    signatures = int(signatures[0].replace(",", ''))

    if not pid:
        pid = page.xpath("//a[@class='load-next no-follow active']/@rel")[0]
    return {
        "pid": pid,
        "title": page.xpath("//h1[@class='title']/text()")[0].strip(),
        "text": "\n".join(page.xpath("//div[@id='petitions-individual']/div/div/p/text()")),
        "tags": page.xpath("//div[@class='issues']/a/text()"),
        "created": created,
        "visited": datetime.now().strftime("%Y-%m-%d-%H:%M:%S"),
        "signatures": signatures,
        "url": "http://petitions.whitehouse.gov" + path
    }

def main():

    parser = argparse.ArgumentParser(description="Retrieve petitions from We The People")
    parser.add_argument("-m", "--max", metavar="INTEGER", dest="max", type=int, default=None,
                        help="maximum number of petitions to retrieve")
    parser.add_argument("-s", "--start", metavar="INTEGER", dest="start", type=int, default=1,
                        help="starting page, 20 per page, default is 1")
    args = parser.parse_args()

    if args.max is not None and args.max < 1:
        parser.error("How can I scrape less than one petition? You make no sense! --max must be one or greater.")

    if args.start < 1:
        parser.error("--start must be one or greater.")

    log("Found %i petitions" % (petitions(args.max, args.start)))
    
    #write log
    scrapelog["end"] = datetime.now().strftime("%Y-%m-%d-%H:%M:%S")
    write(json.dumps(scrapelog, indent=2), "log-" + scrapelog["begin"] + ".json", log_dir())

if __name__ == "__main__":
    main()
