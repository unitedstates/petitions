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
    "signatures": {}
}

def petitions(start=1, mx=None):
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
        
        petitions = page.xpath("body/div[@class]")
        if len(petitions) == 0:
            return hits
            
        for petition in petitions:
            pid = petition.xpath("@id")[0].split('-')[1]
            #get uid for each petition from main div id
            path = petition.xpath("div/div/a/@href")[0]
            data = crawl(path, pid)

            #if petition is dead (unlikely if scanned from WH site directly, but you never know):
            if data["status"] == "expired":
                scrapelog["signatures"][path.split("/")[2]] = -1
            elif data["status"] == "active":
                scrapelog["signatures"][path.split("/")[2]] = data["signature_count"]
                write(json.dumps(data, indent=2, sort_keys=True), "scrape/petitions/" + path.split("/")[2] + ".json")
                hits += 1
                if mx != -1 and hits >= mx:
                    return hits


#visit the page for each petition and get the vitals
def crawl(path, pid=None):
    body = download("http://petitions.whitehouse.gov" + path, path.split('/')[2] + ".html")
    page = etree.parse(StringIO(body), parser)
    #catch page text whether or not petition is still active
    #http://stackoverflow.com/questions/5662404/how-can-i-select-an-element-with-multiple-classes-with-xpath    
    text = "\n".join(page.xpath("//div[contains(concat(' ',@class,' '),' petition-detail')]/p/text()"))
    
    #check if expired
    if "The petition you are trying to access has expired" in text:
        return { "status": "expired" }
    
    #if raw_date not found, probably a bad link (or change in HTML, so we should be careful)
    try:
        raw_date = page.xpath("//div[@class='date']/text()")[0].strip()
    except:
        return { "status": "error", "reason": "no date" }
        
    created = datetime.strptime(raw_date, "%b %d, %Y").strftime("%Y-%m-%d")
    signatures = page.xpath("//div[@class='num-block num-block2']/text()")
    
    #indiciates possible response
    if len(signatures) == 0:
        signatures = page.xpath("//div[@class='num-block']/text()")        
        response = page.xpath("//div[contains(concat(' ',@class,' '),' petition-response')]")
        if response:
            status = "answered"
        else:
            return { "status": "error", "reason": "no signatures"}
    else:
        status = "active"        
    signatures = int(signatures[0].replace(",", ''))    
    
    if not pid:
        #no pid if fewer than 20 signatures        
        try:
            pid = page.xpath("//a[@class='load-next no-follow active']/@rel")[0]
        except:
            pid = "N/A"
        
    return {
        "id": pid,
        "status": status,
        "title": page.xpath("//h1[@class='title']/text()")[0].strip(),
        "body": text,
        "issues": page.xpath("//div[@class='issues']/a/text()"),
        "created": created,
        "visited": datetime.now().strftime("%Y-%m-%d-%H:%M:%S"),
        "signature_count": signatures,
        "url": "http://petitions.whitehouse.gov" + path
    }

def main():
    parser = argparse.ArgumentParser(description="Retrieve petitions from We The People")
    parser.add_argument("-m", "--max", metavar="MAX", dest="max", type=int, default=None,
                        help="maximum number of petitions to retrieve")
    parser.add_argument("-s", "--start", metavar="START", dest="start", type=int, default=1,
                        help="starting page, 20 per page, default is 1")
    args = parser.parse_args()

    if args.max is not None and args.max < 1:
        parser.error("How can I scrape less than one petition? You make no sense! --max must be one or greater.")

    if args.start < 1:
        parser.error("--start must be one or greater.")

    log("Found %i petitions" % (petitions(args.start, args.max)))
    
    #write log
    scrapelog["end"] = datetime.now().strftime("%Y-%m-%d-%H:%M:%S")
    write(json.dumps(scrapelog, indent=2), "log-wh-" + scrapelog["begin"] + ".json", log_dir())

if __name__ == "__main__":
    main()
