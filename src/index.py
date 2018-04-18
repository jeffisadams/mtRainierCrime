import os
import sys
import hashlib
from datetime import datetime

import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

import twitter
import urllib2
from bs4 import BeautifulSoup

# Get our Config
from config import main as conf
config = conf()

# Add the parsers directory to the path
# Import the specific parser based on the environment I'm in.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/parsers/')
import mtrainier as parser


twitterApi = twitter.Api(
  consumer_key=config.get('twitter', 'consumerKey'),
  consumer_secret=config.get('twitter', 'consumerSecret'),
  access_token_key=config.get('twitter', 'accessToken'),
  access_token_secret=config.get('twitter', 'accessTokenSecret')
)

cred = credentials.Certificate(config.get('firebase', 'serviceAccountPath'))
default_app = firebase_admin.initialize_app(cred, {
  'databaseURL': config.get('firebase', 'domain')
})



def tweet(row):
  time = datetime.fromtimestamp(float(row['date'])).strftime("%Y-%m-%d %H:%M")
  textStr = "\n".join([time, row['type'], row['link']])
  twitterApi.PostUpdate(textStr)

'''
Gets the html for a given location
'''
def getHTML(domain = config.get('domain', 'home')):
  response = urllib2.urlopen(domain)
  html = response.read()
  response.close()
  return html

'''
  Gets all related links that are in the same domain
'''
def getLinks(link):
  domain = config.get('domain','home')
  home = BeautifulSoup(getHTML(link), 'html.parser')
  return [link.attrs['href'] for link in home.find_all('a', href=True) if link.attrs['href'].startswith(domain)]

cache = db.reference('cache')
def getCachedLinks():
  cachedLinks = cache.get()
  if cachedLinks is not None:
    cachedLinks = cachedLinks.values()
  else:
    cachedLinks = []
  return cachedLinks

# The procedural Code
# Get all of the links from the site at large

links = getLinks(config.get('domain', 'home'))
# for link in links:
  # myLinks = [link for link in getLinks(link) if link.endswith('html')]
  # links = [item for item in (links + myLinks) if ("mrpd-calls-for-service" in item)]

refinedLinks = [link for link in links if "mrpd-calls-for-service" in link]

count = 0

ref = db.reference('reports')
# Iterate over the links and process the ones we haven't yet
for link in refinedLinks:
  if link not in getCachedLinks():
    print link
    for r in parser.parseHtml(getHTML(link)):
      try:
        if (len(r.items()) > 0) and ('link' in r.keys()):
          key = str(hash(repr(r.items())))
          tweet(r)
          ref.child(key).set(r)
          count = count + 1
        else:
          print("Skipping cause I didn't get an address")
          print(r)
          print("")
      except:
        print("Skipping tweet / save for : ")
        print(r)
        print(sys.exc_info()[0])
    print("Processed So far: ",  count)
    cache.push(link)
  else:
    print "Skipping " + link
