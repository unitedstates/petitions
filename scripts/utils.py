import os, os.path, errno, sys, traceback
import json
import re
import htmlentitydefs
import pprint
import datetime, time
from lxml import html, etree
from pprint import pprint
import logging
from pytz import timezone

import smtplib
import email.utils
from email.mime.text import MIMEText
import getpass


# read in an opt-in config file for changing directories and supplying email settings
# returns None if it's not there, and this should always be handled gracefully

eastern_time_zone = timezone('US/Eastern')

def log(object):
  if isinstance(object, (str, unicode)):
    print object
  else:
    pprint(object)
    
def format_datetime(obj):
  if isinstance(obj, datetime.datetime):
    return eastern_time_zone.localize(obj.replace(microsecond=0)).isoformat()
  elif isinstance(obj, str):
    return obj
  else:
    return None

def write(content, destination):
  mkdir_p(os.path.dirname(destination))
  f = open(destination, 'w')
  f.write(content)
  f.close()

def read(destination):
  if os.path.exists(destination):
    with open(destination) as f:
      return f.read()

# de-dupe a list, taken from:
# http://stackoverflow.com/questions/480214/how-do-you-remove-duplicates-from-a-list-in-python-whilst-preserving-order
def uniq(seq):
  seen = set()
  seen_add = seen.add
  return [ x for x in seq if x not in seen and not seen_add(x)]

import os, errno

# mkdir -p in python, from:
# http://stackoverflow.com/questions/600268/mkdir-p-functionality-in-python
def mkdir_p(path):
  try:
    os.makedirs(path)
  except OSError as exc: # Python >2.5
    if exc.errno == errno.EEXIST:
      pass
    else: 
      raise

def xpath_regex(doc, element, pattern):
  return doc.xpath(
    "//%s[re:match(text(), '%s')]" % (element, pattern), 
    namespaces={"re": "http://exslt.org/regular-expressions"})

# taken from http://effbot.org/zone/re-sub.htm#unescape-html
def unescape(text):

  def remove_unicode_control(str):
    remove_re = re.compile(u'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]')
    return remove_re.sub('', str)

  def fixup(m):
    text = m.group(0)
    if text[:2] == "&#":
      # character reference
      try:
        if text[:3] == "&#x":
          return unichr(int(text[3:-1], 16))
        else:
          return unichr(int(text[2:-1]))
      except ValueError:
        pass
    else:
      # named entity
      try:
        text = unichr(htmlentitydefs.name2codepoint[text[1:-1]])
      except KeyError:
        pass
    return text # leave as is

  text = re.sub("&#?\w+;", fixup, text)
  text = remove_unicode_control(text)
  return text


##### Downloading 

import scrapelib
scraper = scrapelib.Scraper(requests_per_minute=120, follow_robots=False, retry_attempts=3)

# uses config values if present
def cache_dir():
  return os.getcwd() + "/cache"

# uses config values if present
def data_dir():
  return os.getcwd() + "/data"

def download(url, destination, force=False, options=None):
  if not options:
    options = {}

  cache = os.path.join(cache_dir(), destination) 
  
  if not force and os.path.exists(cache):
    if options.get('debug', False):
      log("Cached: (%s, %s)" % (cache, url))

    with open(cache, 'r') as f:
      body = f.read()
  else:
    try:
      if options.get('debug', False):
        log("Downloading: %s" % url)
      response = scraper.urlopen(url)
      body = response.encode('utf-8')
    except scrapelib.HTTPError as e:
      log("Error downloading %s" % url)
      return None

    # don't allow 0-byte files
    if (not body) or (not body.strip()):
      return None

    # cache content to disk
    write(body, cache)

  return body

# if email settings are supplied, email the text - otherwise, just print it
def admin(body):
  try:
    if isinstance(body, Exception):
      body = format_exception(body)

    logging.error(body) # always print it

    if config:
      details = config.get('email', None)
      if details:
        send_email(body)
    
  except Exception as exception:
    print "Exception logging message to admin, halting as to avoid loop"
    print format_exception(exception)

def format_exception(exception):
  exc_type, exc_value, exc_traceback = sys.exc_info()
  return "\n".join(traceback.format_exception(exc_type, exc_value, exc_traceback))

# this should only be called if the settings are definitely there
def send_email(message):
  settings = config['email']

  # adapted from http://www.doughellmann.com/PyMOTW/smtplib/
  msg = MIMEText(message)
  msg.set_unixfrom('author')
  msg['To'] = email.utils.formataddr(('Recipient', settings['to']))
  msg['From'] = email.utils.formataddr((settings['from_name'], settings['from']))
  msg['Subject'] = "%s - %i" % (settings['subject'], int(time.time()))

  server = smtplib.SMTP(settings['hostname'])
  try:
    server.ehlo()
    if settings['starttls'] and server.has_extn('STARTTLS'):
      server.starttls()
      server.ehlo()

    server.login(settings['user_name'], settings['password'])
    server.sendmail(settings['from'], [settings['to']], msg.as_string())
  finally:
    server.quit()

  logging.info("Sent email to %s" % settings['to'])
