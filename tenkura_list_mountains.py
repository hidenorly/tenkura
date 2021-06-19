#   Copyright 2021 hidenorly
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

import sys
import requests
from bs4 import BeautifulSoup

def isMountainLink(url):
  return url.startswith("kad.html?code=")

def getBaseUrl(url):
  baseUrlIndex = url.rfind("/")
  baseUrl = url
  if baseUrlIndex != -1:
    baseUrl =  url[0:baseUrlIndex+1]
  return baseUrl

def getUniqueKeyValue(hashmap, key, value):
  if key in hashmap:
    if hashmap[key]!=value:
      countIndex = key.rfind("_")
      if countIndex != -1:
        count = int( key[countIndex+1:key.len()] ) + 1
        key = key[0:countIndex+1]+str(count)
      else:
        key = key+"_2"
  return key

def getLinks(articleUrl, result):
  if result == None:
    result = {}
  res = requests.get(articleUrl) #  html = urlopen(articleUrl)
  baseUrl = getBaseUrl(articleUrl)
  soup = BeautifulSoup(res.text, 'html.parser') #use html instead of res.text
  tables = soup.find_all("table", {})
  if None != tables:
    for aTable in tables:
      rows = aTable.find_all("tr")
      for aRow in rows:
        links = aRow.findAll("a")
        for aLink in links:
          theUrl = aLink.get("href").strip()
          theText = aLink.get_text().strip()
          if isMountainLink(theUrl):
            value = baseUrl+theUrl
            result[getUniqueKeyValue(result, theText, value)] = baseUrl+theUrl
  return result


if __name__=="__main__":
  links = {}
  mountainLinks = []
  for aLink in sys.argv:
    if aLink.startswith("http"):
      mountainLinks.append( aLink )

  for aMountainLink in mountainLinks:
    links = getLinks(aMountainLink, links)

  print("mountainDic={")
  for theText, theUrl in links.items():
  	print('  "'+theText+'":"'+theUrl+'",')
  print("}")

  print('''
def getMountainDic():
  return mountainDic
''')