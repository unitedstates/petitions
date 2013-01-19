import json
import os
import datetime
import scrapelib
from StringIO import StringIO
from lxml.html import etree, parse
from urlparse import urlparse
from utils import log, download
import urllib

#intialize scraper and parser
s = scrapelib.Scraper(requests_per_minute=60, follow_robots=False)
parser = etree.HTMLParser()

#get current working directory for file system access in Cloud9IDE
cwd = os.getcwd()

def petitions(start=1, mx = -1):
    hits = 0
    #scan WH site, add any new petitions to DB
    #surely a better way to get indefinite number of results than to create a functionally infinite loop, then breaking it, but drawing a blank
    for pg in range(start,1000):
        #The WH site loads petitions from an external HTML doc in a JSON shell
        url = "https://petitions.whitehouse.gov/petitions/more/all/%d/2/0/" % pg
        try:
            raw = s.urlopen(url).encode('utf-8')
        except scrapelib.HTTPError as e:
            print "Error downloading %s" % url
            return
        resp = json.loads(raw)
        if "markup" not in resp or len(resp["markup"]) == 0:
            log("No results at page %i" % pg)
            return
        page = etree.parse(StringIO(resp['markup']), parser)
        #there are two links to each petition in the results, but can reduce to uniques with "nofollow"

        for petition in page.xpath("body/div[@class]"):        
            pid = petition.xpath("@id")[0].split('-')[1]
            #get uid for each petition from main div id
            data = crawl(petition.xpath("div/div/a/@href")[0])
            print data
            return
            #TO DO: add --fast flag for ignore existing petitions
            utils.write(json.dumps(crawl(pid), indent=2), cwd + "/data/" + pid + ".json") 
        exit()
        #print "Found %i petitions on page %i" % (count, pg)
        if count == 0:
            return
        hits += count
        if mx != -1 and hits > mx:
            return

#visit the page for each petition and get the vitals
def crawl(path, pid=None):
    body = download("http://petitions.whitehouse.gov" + path, path.split('/')[2])
    page = etree.parse(StringIO(body), parser)    
    raw_date = page.xpath("//div[@class='date']/text()")[0].strip()
    created = datetime.datetime.strptime(raw_date, "%b %d, %Y").strftime("%Y-%m-%d")
    
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
        "visited": datetime.datetime.strptime(raw_date, "%b %d, %Y").strftime("%Y-%m-%d"),
        "signatures": signatures,
        "url": "http://petitions.whitehouse.gov" + path
    }

petitions()