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

  if url.startswith("https://tkcdn1.n-kishou.co.jp/image/images/kanko/tozan/mnt3.gif"):
    result = "C"
  elif url.startswith("https://tkcdn1.n-kishou.co.jp/image/images/kanko/tozan/mnt2.gif"):
    result = "B"
  elif url.startswith("https://tkcdn1.n-kishou.co.jp/image/images/kanko/tozan/mnt1.gif"):
    result = "A"

  return result

def filterWeather(weatherResult):
  result = []
  result.append(weatherResult[0])

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
    result.append(key)
    result.append(weatherResult[index])

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


if __name__=="__main__":
  argLength = len(sys.argv)
  if  argLength > 1:
    i = 1
    while i < argLength:
      mountains.append( sys.argv[i] )
      i = i + 1

  for aMountain in mountains:
    mountainKeys = getMountainKeys(aMountain)
    for theMountain in mountainKeys:
      print( theMountain + " : " )
      result = getWeather( mountainDic[theMountain] )
      for aResult in result:
        print( aResult )





