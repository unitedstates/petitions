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

def assemble(pid, roster, overwrite=False):
    if not overwrite:
        try: 
            info = json.load(open(os.getcwd() + "/data/api/signatures/" + pid + "/info.json", "r"))
            return info
        except Exception, e:
            print "No info file found for petition %s. Computing" % pid
    
    signatures = []
    for filenm in [x for x in os.listdir(os.getcwd() + "/data/api/signatures/%s/" % pid) if len(x) > 11]:
        signatures += json.load(open(os.getcwd() + "/data/api/signatures/%s/%s" % (pid, filenm), 'r'))
        
    zips = [x for x in signatures if x["zip"] and x["zip"] != "" and x["name"] and x["name"] != ""]
    log("Found names and zip codes for %i percent of signatures on petition %s" % (100 * len(zips) / len(signatures), pid))
    uniques = ["%s_%s" % (x['name'], x['zip']) for x in zips]
    
    info = {
        "total": len(signatures),
        "zips": len(uniques),
        "duplicates": list(set([(x, uniques.count(x)) for x in uniques if uniques.count(x) > 1])),
        "uniques": list(set(uniques))
    }

    write(json.dumps(info, indent=2), "api/signatures/%s/info.json" % pid)

    #print duplicates
    #uniques = set(uniques)

    '''
    for person in uniques:
        roster[person].append(pid)
    '''
    
    return info

def get_roster(mx, offset, startat):
    roster = defaultdict(list)
    total = 0
    petitions = [x for x in os.listdir("data/api/petitions/") if x[-5:] == ".json"]
    if startat and startat + ".json" in petitions:
        offset = petitions.index(startat + ".json")
    petitions = petitions[offset:]
    
    if mx != -1:
        petitions = petitions[:mx]

    for petition in petitions:
        total += assemble(petition[:-5], roster)["total"]
    
    '''
    multis = [x for x in roster.items() if len(x[1]) > 1]
    
    report = {
        'total': total,
        'uniques': len(roster.items()),
        'petitions': petitions,
        'multis': sorted(multis, key=lambda x:len(x[1]), reverse=True)
    }
    
    write(json.dumps(multis, indent=2), "api/reports/multis.json")
    '''
    
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
    parser.add_argument("-i", "--id", dest="pid", type=str, default=None,
                        help="the id of a single petition to crawl")

    args = parser.parse_args()
    
    #HumanError catch
    if args.max != -1 and args.max < 1:
        parser.error("How can I scrape less than one petition? You make no sense! --max must be one or greater.")
    if args.start < 0:
        parser.error("--start must be zero or greater.")
        
    #function calls    
    if args.task == "network":
        if args.pid:
            roster = assemble(args.pid, defaultdict(list))
        else:
            roster = get_roster(args.max, args.start, args.startat)
            print "done"
if __name__ == "__main__":
    main()