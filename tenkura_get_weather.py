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
import argparse
import unicodedata
from bs4 import BeautifulSoup
import mountainDic

mountains = []
mountainDic = mountainDic.getMountainDic()

def getMountainKeys(key):
  result = []
  for dicKey, value in mountainDic.items():
    if dicKey.startswith(key):
      result.append( dicKey )
  return result

def getClimbScore(url):
  result = None

  if url.endswith("mnt3.gif"):
    result = "C"
  elif url.endswith("mnt2.gif"):
    result = "B"
  elif url.endswith("mnt1.gif"):
    result = "A"

  return result

def filterWeather(weatherResult):
  result = {}
  candidates = {}

  i=0
  for text in weatherResult:
    i=i+1
    nResultLen = len(weatherResult)
    if isinstance(text, str):
      if text.find("今 日  ")!=-1 or text.find("明 日  ")!=-1 or text == "週　間　予　報" :
        currentLength = 0
        if text in candidates:
          currentLength = candidates[text]
        if i<nResultLen and isinstance(weatherResult[i], list):
          if len(weatherResult[i]) > currentLength:
            candidates[text] = i

  for key, index in candidates.items():
    result[key] = weatherResult[index]

  return result

def getWeather(url):
  result = []
  theDay = []
  result.append( url )

  res = requests.get(url)
  soup = BeautifulSoup(res.text, 'html.parser')
  tables = soup.find_all("table")#, class_='only-pc')
  if None != tables:
    for aTable in tables:
      rows = aTable.find_all("tr")
      theDay = []
      if None != rows:
        for aRow in rows:
          cols = aRow.find_all("td")
          if None != cols:
            for aCol in cols:
              text = aCol.getText().strip()
              if( text.find("今 日  ")!=-1 or text.find("明 日  ")!=-1 or text == "週　間　予　報"):
                result.append(text)
              imgs = aCol.find_all("img")
              for anImg in imgs:
                theUrl = anImg.get("src").strip()
                if anImg.get("alt") == "登山指数":
                  climbScore = getClimbScore(theUrl)
                  if( None != climbScore ):
                    theDay.append(climbScore)
      if len(theDay) != 0:
        result.append( theDay )

  return filterWeather(result)

def ljust_jp(value, length, pad = " "):
  count_length = 0
  for char in value.encode().decode('utf8'):
    if ord(char) <= 255:
      count_length += 1
    else:
      count_length += 2
  return value + pad * (length-count_length)


if __name__=="__main__":
  parser = argparse.ArgumentParser(description='Parse command line options.')
  parser.add_argument('args', nargs='*', help='mountain name such as 富士山')
  parser.add_argument('-c', '--compare', action='store_true', help='compare mountains per day')
  args = parser.parse_args()

  if len(args.args) == 0:
    parser.print_help()
    exit(-1)

  mountains = args.args

  mountainWeathers={}
  for aMountain in mountains:
    mountainKeys = getMountainKeys(aMountain)
    for theMountain in mountainKeys:
      mountainWeathers[ theMountain ] = getWeather( mountainDic[theMountain] )

  if False == args.compare:
    for aMountain, theWeather in mountainWeathers.items():
      print( aMountain + " : " )
      for key, value in theWeather.items():
        print( key + ":" + " ".join(map(str, value)) )
  else:
    dispKeys = {}
    for aMountain, theWeather in mountainWeathers.items():
      for key, value in theWeather.items():
        dispKeys[key] = True

    for aDispKey in dispKeys.keys():
      print( aDispKey )
      for aMountainName, theWeather in mountainWeathers.items():
        if aDispKey in theWeather:
          print( ljust_jp(aMountainName, 20) + ": " + " ".join(map(str, theWeather[aDispKey])) )
      print( "" )






