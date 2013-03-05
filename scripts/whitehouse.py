#!/usr/bin/env python
import os
import sys
import json
import datetime
import urllib, urllib2
from itertools import combinations
from collections import defaultdict 
from utils import log, download, write, log_dir
import argparse

BASEURI="https://petitions.whitehouse.gov/api/v1/petitions"
BASEURL="https://petitions.whitehouse.gov/api/v1/petitions.json?"

#joint APIKEY provided by WH. If not present, load from keys.json
APIKEY='aVmupNPJmgkweR9'

if APIKEY == '':
    try:
        keychain = json.load(open(os.getcwd() + "/scripts/keys.json", "r"))
    except:
        print "You need a file in the scripts directory called keys.json"
        sys.exit()
    
    if "whitehouse" not in keychain:
        print "You need a whitehouse API key in keys.json"
        sys.exit()
    
    APIKEY = keychain['whitehouse']

# Basic wrapper
# h/t https://github.com/WhiteHouse/hackathon/blob/master/petitions-api-examples/pytition/pytition.py

def fetch_petitions(start,num):
    tmpURL = BASEURL + "key=" + APIKEY + "&limit=" + str(num) + "&offset=" + str(start)
    tmpResponse = urllib2.urlopen(tmpURL)
    if tmpResponse.code != 200:
        print "Error retrieving results from %s" % tmpURL
    try:
        tmpData = json.loads(tmpResponse.read())
    except:
        print "Couldn't decode JSON from this:"
        print tmpResponse
        return {}
    return tmpData

def fetch_signatures(pid, limit, offset):
    #/api/v1/petitions/petition_id/signatures.json?limit=100&offset=0
    tmpURL = BASEURI + "/" + pid + "/signatures.json?limit=%d&offset=%d&" % (limit, offset) + "key=" + APIKEY 
    tmpResponse = urllib2.urlopen(tmpURL).read()
    tmpData = json.loads(tmpResponse)
    return tmpData

#load the ids for all open petitions
def get_petitions(mx=-1, offset=0):
    limit = 100
    stop = False
    petitions = []
    
    while not stop:
        data = fetch_petitions(offset, limit)     
        if "results" not in data or len(data["results"]) == 0:
            stop = True
            continue
        petitions += data["results"]
        if mx > -1 and len(petitions) > mx:
            petitions = petitions[:mx]
            stop = True

        offset += limit

    for petition in petitions:
        write(json.dumps(petition, indent=2), "api/petitions/" + petition['id'] + ".json")

    return petitions

#get every signature for a given petition
def get_petition_signatures(pid, write_all=False):
    limit = 1000
    offset = 0
    signatures = []
    stop = False
    while not stop:
        resp = fetch_signatures(pid, limit, offset)
        if "results" not in resp or len(resp['results']) == 0:
            stop = True
        else:
            signatures += resp["results"]
            offset += limit
            
    if len(signatures) > 0 and write_all:
        write(json.dumps(signatures), "api/signatures/" + pid + ".json")
    
    split_signatures(pid, signatures)
    
    return signatures

def split_signatures(pid, signatures=None):
    if not signatures:
        signatures = json.load(open(os.getcwd() + "/data/api/signatures/" + pid + ".json", "r"))
        
    for signature in signatures:
        signature['date'] = datetime.datetime.fromtimestamp(signature['created']).strftime("%y-%m-%d")
        signature['time'] = datetime.datetime.fromtimestamp(signature['created']).strftime("%H:%M:%S")
        #rm this needless field
        if signature['type'] == "signature":
            signature.pop("type")

    dates = sorted(set(map(lambda x:x['date'], signatures)))
    stats = { 'total': len(signatures), 'dates': [], 'last' : signatures[0]['created'] }
    for day in dates:
        sigs = [x for x in signatures if x['date'] == day]
        stats['dates'].append((day, len(sigs)))
        write(json.dumps(sigs), "api/signatures/" + pid + "/" + day + ".json")
        
    write(json.dumps(stats, indent=2), "api/signatures/" + pid + "/stats.json")

def get_signatures(mx, offset, startat):
    petitions = [x for x in os.listdir("data/api/petitions/") if x[-5:] == ".json"]
    if startat and startat + ".json" in petitions:
        offset = petitions.index(startat + ".json")
        print offset
    petitions = petitions[offset:]
    
    if mx != -1:
        petitions = petitions[:mx]
        
    for filenm in petitions:
        petition = json.load(open("data/api/petitions/" + filenm))
        print "Searching signatures for %s, expecting %i" % (petition['id'], petition['signature count'])
        signatures = get_petition_signatures(petition['id'])
        print "Found %i signatures for petition with id %s" % (len(signatures), petition['id'])
        
def main():
    parser = argparse.ArgumentParser(description="Retrieve petitions from the We The People API")
    parser.add_argument(metavar="TASK", dest="task", type=str, default="petitions",
                        help="which task to run: petitions, signatures")
    parser.add_argument("-m", "--max", metavar="INTEGER", dest="max", type=int, default=-1,
                        help="maximum number of petitions to retrieve")
    parser.add_argument("-s", "--start", metavar="INTEGER", dest="start", type=int, default=0,
                        help="starting page, 20 per page, default is 1")
    parser.add_argument("-a", "--startat", dest="startat", type=str, default=None,
                        help="if of the first petition to crawl, in leiu of --start")
                        
    args = parser.parse_args()

    if args.max != -1 and args.max < 1:
        parser.error("How can I scrape less than one petition? You make no sense! --max must be one or greater.")

    if args.start < 0:
        parser.error("--start must be zero or greater.")

    if args.task == "petitions":
        log("Found %i petitions" % (len(get_petitions(args.max, args.start))))
    elif args.task == "signatures":
        get_signatures(args.max, args.start, args.startat)

    else:
        parser.error("I don't recognize that task! I only recognize 'petitions' and 'signatures'")

    #write log
    #scrapelog["end"] = datetime.now().strftime("%Y-%m-%d-%H:%M:%S")
    #write(json.dumps(scrapelog, indent=2), "log-wh-" + scrapelog["begin"] + ".json", log_dir())


if __name__ == "__main__":
    main()