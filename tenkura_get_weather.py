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

weatherStatusDic={
  "00":"fine",
  "01":"fine_cloud",
  "02":"fine_rain",
  "03":"fine_rain",
  "04":"fine_snow",
  "05":"fine_snow",
  "06":"fine_cloud",
  "07":"fine_rain",
  "08":"fine_snow",
  "09":"fine_rain_thunder",
  "10":"fine_cloud",
  "11":"cloud",
  "12":"cloud_fine",
  "13":"cloud_rain",
  "14":"cloud_rain",
  "15":"cloud_snow",
  "16":"cloud_snow",
  "17":"snow",
  "18":"cloud_fine",
  "19":"cloud_rain",
  "20":"cloud_snow",
  "21":"cloud_snow",
  "22":"cloud_thunder",
  "23":"cloud_snow_thunder",
  "24":"rain",
  "25":"rain_fine",
  "26":"rain_cloud",
  "27":"rain_snow",
  "28":"rain_fine",
  "29":"rain_cloud",
  "30":"rain_snow",
  "31":"rain_thunder",
  "32":"snow",
  "33":"snow_fine",
  "34":"snow_cloud",
  "35":"snow_rain",
  "36":"snow_fine",
  "37":"snow_cloud",
  "38":"snow_rain",
  "39":"snow_thunder",
  "40":"fine",
  "41":"fine_cloud",
  "42":"fine_rain",
  "43":"fine_rain",
  "44":"snow_fine",
  "45":"snow_fine",
  "46":"fine_cloud",
  "47":"fine_rain",
  "48":"fine_snow",
  "49":"fine_rain_thunder",
  "50":"fine_cloud",
  "51":"cloud_fine",
  "52":"cloud_fine",
  "53":"rain_fine",
  "54":"rain_fine",
  "55":"snow_fine",
  "56":"snow_fine",
}

def getWeatherString(weatherStatus):
  result = ""
  if weatherStatus in weatherStatusDic:
    result = weatherStatusDic[weatherStatus]
  return result

def getWeatherScore(url):
  result = None
  if url.find("/tenkim/")!=-1 and url.endswith(".gif"):
    weatherIcon = url[url.rfind("/")+2:len(url)-4]
    result = str.ljust(getWeatherString(weatherIcon), 10)

  return result

def getFormatedKeyString(text):
  result = text
  result = result.replace("週　間　予　報", "週間予報")
  return result

def filterWeather(weatherResult):
  result = {}
  candidates = {}

  nResultLen = len(weatherResult)
  foundWeek = False
  modeClimb = True
  key = ""

  i=0
  for text in weatherResult:
    currentLength = 0

    if isinstance(text, str):
      prevModeClimb = modeClimb
      if text.find("登山")!=-1:
        modeClimb = True
      if text.find("天気")!=-1:
        modeClimb = False
      if modeClimb != prevModeClimb:
        foundWeek = False

      if ( text.find("/")!=-1 and text.find("(")!=-1 and text.find(")")!=-1 ) or text.find("週　間　予　報")!=-1 :
        text = getFormatedKeyString(text)
        if not foundWeek:
          if text.find("週間予報")!=-1:
            foundWeek = True
            key = text
          else:
            key = text

    if key in candidates:
      currentLength = candidates[key]

    i=i+1
    if i<nResultLen and isinstance(weatherResult[i], list):
      if len(weatherResult[i]) > currentLength:
        candidates[key] = i

  for key, index in candidates.items():
    result[key] = weatherResult[index]

  result["url"] = weatherResult[0]

  return result

def maintainResult(result, separator):
  theValue = result[len(result)-1]
  if isinstance(theValue, str) and theValue.startswith("_"):
    result[len(result)-1] = separator + theValue

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
              if ( text.find("/")!=-1 and text.find("(")!=-1 and text.find(")")!=-1 and text.find("風(m/s)")==-1) or text.find("週　間　予　報")!=-1:
                result.append("_"+text)
              imgs = aCol.find_all("img")
              for anImg in imgs:
                theUrl = anImg.get("src").strip()
                imgAlt = anImg.get("alt").strip()
                if imgAlt == "登山指数":
                  climbScore = getClimbScore(theUrl)
                  if None != climbScore :
                    theDay.append(climbScore)
                    maintainResult(result, "登山")
                elif imgAlt == "天気":
                  weatherScore = getWeatherScore(theUrl)
                  if None != weatherScore :
                    theDay.append(weatherScore)
                    maintainResult(result, "天気")
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

def getCategory(key):
  index = key.find("_")
  if index!=-1:
    key = key[0:index]
  return key

def get_max_length_per_category(categorizedData):
  result={}
  for key, theData in categorizedData.items():
    if isinstance(theData, dict):
      for key, data in theData.items():
        if key!="url" and key!="score":
          key = getCategory(key)
          data = " ".join(map(str, data))
          theLen = len(data)
          if ((key in result) and (result[key] < theLen)) or not (key in result):
            result[key] = theLen
  return result

def getRecommendationScore(value):
  if "A" == value:
    return 2
  elif "B" == value:
    return 1
  elif "C" == value:
    return 0
  elif value == "fine":
    return 3
  elif value.find("rain")!=-1:
    return 0
  elif value.find("fine")!=-1:
    return 2
  elif value.find("cloud")!=-1:
    return 1
  return 0

def addingScoringMountain( mountain, scoreKey ):
  if scoreKey:
    score = 0
    for key,value in mountain.items():
      if key.find(scoreKey)!=-1:
        if isinstance(value, list):
          for aData in value:
            score = score + getRecommendationScore(aData)
    mountain["score"] = score
  return mountain


if __name__=="__main__":
  parser = argparse.ArgumentParser(description='Parse command line options.')
  parser.add_argument('args', nargs='*', help='mountain name such as 富士山')
  parser.add_argument('-c', '--compare', action='store_true', help='compare mountains per day')
  parser.add_argument('-s', '--score', action='store', help='specify score key e.g. 登山_明日, 天気_今日, etc.')
  args = parser.parse_args()

  if len(args.args) == 0:
    parser.print_help()
    exit(-1)

  mountains = args.args

  mountainWeathers={}
  for aMountain in mountains:
    mountainKeys = getMountainKeys(aMountain)
    for theMountain in mountainKeys:
      mountainWeathers[ theMountain ] = addingScoringMountain( getWeather( mountainDic[theMountain] ), args.score )

  perKeyMaxLengths = get_max_length_per_category(mountainWeathers)
  nonDispKeys = ["url", "score"]

  if False == args.compare:
    for aMountain, theWeather in mountainWeathers.items():
      print( aMountain + " : " )
      for key, value in theWeather.items():
        if not key in nonDispKeys:
          thePaddingLength = 0
          theDispData = " ".join(map(str, value))
          if key.startswith("登山") and not key.endswith("週間予報"):
            theCategoryKey = getCategory(key)
            thePaddingLength = perKeyMaxLengths[theCategoryKey] - len(theDispData)
          print( ljust_jp(key, 20) + ": " + " "*thePaddingLength + theDispData )
        else:
          print( key.ljust(20) + ": " + str(value) )
      print( "" )
  else:
    dispKeys = {}
    for aMountain, theWeather in mountainWeathers.items():
      for key, value in theWeather.items():
        dispKeys[key] = True

    for aDispKey in dispKeys.keys():
        if not aDispKey in nonDispKeys:
          print( aDispKey )
          for aMountainName, theWeather in mountainWeathers.items():
            if aDispKey in theWeather and not aDispKey in nonDispKeys:
              theDispData = " ".join(map(str, theWeather[aDispKey]))
              thePaddingLength = 0
              if aDispKey.startswith("登山") and not aDispKey.endswith("週間予報"):
                theCategoryKey = getCategory(aDispKey)
                thePaddingLength = perKeyMaxLengths[theCategoryKey] - len(theDispData)
              print( ljust_jp(aMountainName, 20) + ": " + " "*thePaddingLength + theDispData )
          print( "" )

    for aDispKey in nonDispKeys:
      print(aDispKey+":")
      for aMountainName, theWeather in mountainWeathers.items():
        if aDispKey in theWeather:
          print( ljust_jp(aMountainName, 20) + ": " + str( theWeather[aDispKey] ) )
      print( "" )
