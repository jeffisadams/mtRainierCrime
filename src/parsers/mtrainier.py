import os
import sys
from time import sleep
from datetime import datetime

import json

import urllib
import urllib2

from bs4 import BeautifulSoup

from config import main as conf
config = conf()


'''
Parses the html table and gets the value as a dictionary with cleaned values
'''
def parseHtml(html):
  soup = BeautifulSoup(html, 'html.parser')
  # print(soup.find('a', attrs={'class': 'blog-pager-older-link'}).get('href'))
  rows = []
  for row in soup.find('table').find('tbody').find_all('tr', recursive=False):
    try:
      rows.append(processRow([x.text.strip() for x in row.find_all('td', recursive=False)]))
    except:
      print("Skipping row: ")
      print([x.text.strip() for x in row.find_all('td', recursive=False)])
      print(sys.exc_info()[0])
  return rows


'''
  Adds the google maps link, the month day year info, and the lat lng
  Also cleans the address removing some of the marks.
'''
def processRow(row):
  rowDict = {}
  date = datetime.strptime(row[0] + " " + row[1], "%m/%d/%Y %H:%M")
  rowDict['date'] = date.strftime('%s')
  rowDict['month'] = date.strftime('%m')
  rowDict['year'] = date.strftime('%Y')
  rowDict['day'] = date.strftime('%d')
  rowDict['type'] = row[2]
  rowDict['zipcode'] = config.get('location', 'zipcode')
  rowDict['address'] = cleanAddress(row[3])
  
  geocodeReturn = getGeoCode(rowDict['address'], 20712)
  if geocodeReturn is not None:
    rowDict['location'] = geocodeReturn[0]
    rowDict['address'] = geocodeReturn[1]
    rowDict['link'] = "{0}/{1}".format(config.get('google', 'placeLink'), urllib.quote_plus(rowDict['address']))
  return rowDict


'''
  Takes the address and removes some values we don't want.
'''
def cleanAddress(text):
  return text.encode('ascii', 'ignore').lower().replace('/', 'and').replace(' sb', '').replace(' nb', '').split('-')[0]


'''
  Gets the address and precise longitude of the call
'''
def getGeoCode(address, zipcode):
  mapsDomain = config.get('google', 'mapsHost')
  query = urllib.urlencode({
    "address": address + " " +  str(zipcode),
    "key": config.get("google", "apiKey")
  })
  url = "{0}?{1}".format(mapsDomain, query)
  response = urllib2.urlopen(url)
  mapRet = response.read()
  response.close()
  resJson = json.loads(mapRet)
  if len(resJson['results']) > 0:
    return [resJson['results'][0]['geometry']['location'], resJson['results'][0]['formatted_address']]
  else:
    return None