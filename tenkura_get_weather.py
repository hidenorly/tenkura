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
import datetime
import csv
import itertools
import os

from bs4 import BeautifulSoup

import mountainDic
import mountainInfoDic

mountains = []
mountainDic = mountainDic.getMountainDic()
mountainInfoDic = mountainInfoDic.getMountainInfoDic()

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
  result = result.replace("明 日", "明日")
  result = result.replace("あさって", "明後日")
  result = result.replace("  ", ":")
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


def getMountainDetailInfo(mountainName):
  result = None

  if( mountainName in mountainInfoDic):
    result = mountainInfoDic[mountainName]
  else:
    pos = mountainName.find("_")
    if pos != -1:
      mountainName = mountainName[0 : pos - 1 ]
    pos = mountainName.find("（")
    if pos != -1:
      mountainName = mountainName[0 : pos - 1 ]
    for aMountainName, anInfo in mountainInfoDic.items():
      if aMountainName.find( mountainName )!=-1:
        result = anInfo
        break

  return result


def printMountainDetailInfo(mountainName):
  info = getMountainDetailInfo( mountainName )
  if info!=None:
    print( ljust_jp(" altitude", 20) + ": " + info["altitude"] )
    print( ljust_jp(" area", 20) + ": " + info["area"] )
    print( ljust_jp(" difficulty", 20) + ": " + info["difficulty"] )
    print( ljust_jp(" fitnessLevel", 20) + ": " + info["fitnessLevel"] )
    print( ljust_jp(" type", 20) + ": " + info["type"] )
    print( "" )


def getTimeIndex(timeHH):
  result = int(timeHH / 3)
  result = result % 9
  return result

def getTimeRangeFilter(climbRates, startTime, endTime):
  startIndex = getTimeIndex(startTime)
  endIndex = getTimeIndex(endTime)
  if startIndex > endIndex:
    startIndex, endIndex = endIndex, startIndex
  if len(climbRates) == 8:
    climbRates = climbRates[startIndex:endIndex]
  return climbRates

def getTimeRange(timeRange):
  startTime = 0
  endtime = 24
  pos = timeRange.find("-")
  if pos!=-1:
    startTime = int( timeRange[0:pos] )
    endTime = int( timeRange[pos+1:len(timeRange)] )
  else:
    startTime = int( int(timeRange) / 3 ) * 3
    endTime = startTime + 2
  return startTime, endTime

def isClimbRate(climbData):
  result = False

  if hasattr(climbData, "__iter__"):
    result = True
    for aData in climbData:
      if not (aData=="A" or aData=="B" or aData=="C"):
        result = False
        break

  return result

def getStandardizedKey(key):
  result = key
  pos = key.find(":")
  if pos!=-1:
    result = key[pos+1:len(key)]
  if key.endswith("週間予報"):
    result = "weekly"
  return result

def getHashArrayMaxLength(hashArrayData):
  result = 0
  if hasattr(hashArrayData, "__iter__"):
    for key, anArrayData in hashArrayData.items():
      if hasattr(anArrayData, "__iter__"):
        nLen = len(anArrayData)
        if result < nLen:
          result = nLen

  return result

def getLengthEnsuredArrayWithFrontPadding(hashArrayData):
  nEnsuredSize = getHashArrayMaxLength(hashArrayData)
  result = {}
  for key, anArrayData in hashArrayData.items():
    if hasattr(anArrayData, "__iter__"):
      nLen = len(anArrayData)
      nFrontPadding = nEnsuredSize - nLen
      theData = []
      if nFrontPadding>0:
        for i in range(nFrontPadding):
          theData.append("")
      theData.extend( anArrayData )
      result[key] = theData
  return result

def getStandardizedMountainData(weatherData):
  result = {}
  result["climbRate"]={}
  result["climbRate_weekly"]={}
  result["weather"]={}
  result["weather_weekly"]={}
  result["misc"]={}

  for key, aData in weatherData.items():
    rootKey = "weather"
    if isClimbRate(aData):
      rootKey = "climbRate"
    key = getStandardizedKey(key)

    if key=="weekly":
      if isClimbRate(aData):
        rootKey = "climbRate_weekly"
      else:
        rootKey = "weather_weekly"
    elif key=="url":
      rootKey = "misc"
    result[rootKey][key] = aData


  result["climbRate"] = getLengthEnsuredArrayWithFrontPadding(result["climbRate"])
  result["weather"] = getLengthEnsuredArrayWithFrontPadding(result["weather"])

  return result

def frontPaddingStr(str, length):
  thePaddingLength = length - len(str)
  return " "*thePaddingLength + str

def printKeyArray(key, keyLength, arrayData, padding=" ", lPadding=""):
  key = ljust_jp(key, keyLength-len(lPadding))
  val = ""
  for aData in arrayData:
    if aData == "":
      aData=padding
    val = val + aData + padding
  print( lPadding + key + ": " + val )

def getDate(key):
  month = ""
  day = ""

  pos = key.find("/")
  if pos!=-1:
    month = key[0:pos]

    pos2 = key.find("(")
    if pos2!=-1:
     day = key[pos+1:pos2]
    else:
     day = key[pos+1:len(key)]

  return month, day

def isRobustNumeric(data):
  if data is not None:
    try:
      float(data)
    except ValueError:
      return False
    return True
  else:
    return False

def getDateScore(key):
  result = 0
  month, day = getDate( key )
  if month!="" and day!="" and isRobustNumeric(month) and isRobustNumeric(day):
    result = int( month ) * 31 + int( day )
  return result

def isMatchedDate(key, targetDateMMDD):
  result = False
#  pos = key.find( targetDateMMDD )
#  if pos!=-1 or targetDateMMDD=="":
#    result = True
  if targetDateMMDD=="" or getDateScore(key) == getDateScore(targetDateMMDD):
    result = True

  return result

def getMaxDateMMDD(climbRates):
  result = ""
  score = 0
  for key, arrayData in climbRates.items():
    currentScore = getDateScore(key)
    if currentScore > score:
      score = currentScore
      month, day = getDate( key )
      result = month + "/" + day
  return result

def getDateTimeFromMMDD(mmdd):
  if mmdd=="":
    mmdd="1/1"
  thisYear = datetime.datetime.now().strftime("%Y")
  return datetime.datetime.strptime(thisYear + "/" + mmdd, "%Y/%m/%d")

def getDateRangeFilterForWeek(weeklyArrayData, startDateTime, targetDateTime):
  result = []
  currentDateTime = startDateTime
  for aData in weeklyArrayData:
    if currentDateTime == targetDateTime:
      result.append( aData )
    currentDateTime = currentDateTime + datetime.timedelta(days=1)

  return result

def isAcceptableClimbRateRange( arrayData, acceptableClimbRates ):
  result = True
  acceptableClimbRates = acceptableClimbRates.split(",")
  for aData in arrayData:
    isOk = False
    for anAcceptableRate in acceptableClimbRates:
      if aData == anAcceptableRate:
        isOk = True
        break
    if not isOk:
      result = False
      break

  return result

def dumpPerMountain(mountainWeathers, nonDispKeys, targetDateMMDD, startTime, endTime, acceptableClimbRates):
  for aMountain, theWeather in mountainWeathers.items():
    stadndarizedData = getStandardizedMountainData(theWeather)

    # print detail climb rate
    found = False
    for key, arrayData in stadndarizedData["climbRate"].items():
      if isMatchedDate( key, targetDateMMDD ):
        arrayData = getTimeRangeFilter( arrayData, startTime, endTime )
        if isAcceptableClimbRateRange( arrayData, acceptableClimbRates ):
          if not found:
            print( aMountain + " : " )
            found = True
          printKeyArray( key, 20, arrayData, lPadding=" ")

    # print weekly climb rate
    climbRateDayMax = getMaxDateMMDD( stadndarizedData["climbRate"] )
    if climbRateDayMax!="":
      climbRateDayMax_dateTime = getDateTimeFromMMDD( climbRateDayMax )
      weekStart_dateTime = climbRateDayMax_dateTime + datetime.timedelta(days=1)

      if ( "climbRate_weekly" in stadndarizedData ) and ( "weekly" in stadndarizedData["climbRate_weekly"] ):
        weeklyData = stadndarizedData["climbRate_weekly"]["weekly"]
        if targetDateMMDD!="":
          weeklyData = getDateRangeFilterForWeek( weeklyData, weekStart_dateTime, getDateTimeFromMMDD(targetDateMMDD) )
        if len( weeklyData )!=0:
          if isAcceptableClimbRateRange( weeklyData, acceptableClimbRates ):
            if not found:
              print( aMountain + " : " )
              found = True
            printKeyArray( "weekly", 20, weeklyData, lPadding=" ")

    if found:
      # print detail weather rate
      for key, arrayData in stadndarizedData["weather"].items():
        if isMatchedDate( key, targetDateMMDD ):
          arrayData = getTimeRangeFilter( arrayData, startTime, endTime )
          printKeyArray( key, 20, arrayData, lPadding=" ")

      # print misc.
      printKeyArray( "url", 20, stadndarizedData["misc"]["url"], "", lPadding=" " )

      # print mountain detail
      printMountainDetailInfo( aMountain )

      print("")

def dumpPerCategory(mountainWeathers, nonDispKeys, targetDateMMDD, startTime, endTime, acceptableClimbRates):
  dispKeys = {}
  dispCategory = {}
  standarizedData = {}
  for aMountain, theWeather in mountainWeathers.items():
    standarizedData[aMountain] = getStandardizedMountainData(theWeather)
    for key, value in standarizedData[aMountain].items():
      dispCategory[key] = True
      for key2, value2 in value.items():
        dispKeys[key2] = True

  displayedMountains={}

  # display per category data
  foundData = False
  for aCategoryKey in dispCategory.keys():
    for aDispKey in dispKeys.keys():
        if not aDispKey in nonDispKeys:
          found = False
          for aMountainName, aStandarizedData in standarizedData.items():
            if (aCategoryKey in aStandarizedData) and (aDispKey in aStandarizedData[aCategoryKey]):# and not (aDispKey in nonDispKeys):
              if isMatchedDate( aDispKey, targetDateMMDD ):
                arrayData = aStandarizedData[aCategoryKey][aDispKey]
                if aCategoryKey == "climbRate" or aCategoryKey == "weather":
                  if isMatchedDate( aDispKey, targetDateMMDD ):
                    arrayData = getTimeRangeFilter( arrayData, startTime, endTime )
                if ( isClimbRate( arrayData ) and not isAcceptableClimbRateRange( arrayData, acceptableClimbRates ) ):
                  continue
                else:
                  if found == False:
                    print( "" )
                    print( aCategoryKey + ":" + aDispKey )
                    found = True
                  printKeyArray( aMountainName, 20, arrayData, lPadding=" " )
                  displayedMountains[aMountainName] = True
                  foundData = True

  # fallback
  if foundData==False:
    weekStart_dateTime = None
    for aMountainName, aStandarizedData in standarizedData.items():
      climbRateDayMax = getMaxDateMMDD( aStandarizedData["climbRate"] )
      if climbRateDayMax!="":
        climbRateDayMax_dateTime = getDateTimeFromMMDD( climbRateDayMax )
        weekStart_dateTime = climbRateDayMax_dateTime + datetime.timedelta(days=1)
        break

    if weekStart_dateTime!=None:
      for aMountainName, aStandarizedData in standarizedData.items():
        if ( "climbRate_weekly" in aStandarizedData ) and ( "weekly" in aStandarizedData["climbRate_weekly"] ):
          weeklyData = aStandarizedData["climbRate_weekly"]["weekly"]
          if targetDateMMDD!="":
            weeklyData = getDateRangeFilterForWeek( weeklyData, weekStart_dateTime, getDateTimeFromMMDD(targetDateMMDD) )
          if len( weeklyData )!=0:
            if isAcceptableClimbRateRange( weeklyData, acceptableClimbRates ):
              if foundData == False:
                print( "climbRate_weekly:"+targetDateMMDD )
                foundData = True
              printKeyArray( aMountainName, 20, weeklyData, lPadding=" ")
              displayedMountains[aMountainName] = True

  if foundData:
    # display detail information
    print( "" )
    for aDispKey in nonDispKeys:
      print(aDispKey+":")
      for aMountainName, flag in displayedMountains.items():
        theWeather = mountainWeathers[aMountainName]
        if aDispKey in theWeather:
          print( ljust_jp(aMountainName, 20) + ": " + str( theWeather[aDispKey] ) )
          printMountainDetailInfo( aMountainName )
      print( "" )

def openCsv( fileName, delimiter="," ):
  result = []
  if os.path.exists( fileName ):
    file = open( fileName )
    if file:
      reader = csv.reader(file, quoting=csv.QUOTE_MINIMAL, delimiter=delimiter)
      for aRow in reader:
        data = []
        for aCol in aRow:
          aCol = aCol.strip()
          if aCol.startswith("\""):
            aCol = aCol[1:len(aCol)]
          if aCol.endswith("\""):
            aCol = aCol[0:len(aCol)-1]
          data.append( aCol )
        result.append( data )
  return result

def isMatchedMountainRobust(arrayData, search):
  result = False
  for aData in arrayData:
    if aData.find(search)!=-1 or search.find(aData)!=-1:
      result = True
      break
  return result


def mountainsIncludeExcludeFromFile( mountains, excludeFile, includeFile ):
  result = []
  excludes = list( itertools.chain.from_iterable( openCsv( excludeFile ) ) )
  includes = list( itertools.chain.from_iterable( openCsv( includeFile ) ) )
  for aMountain in includes:
    mountains.append( aMountain )
  for aMountain in mountains:
    if not isMatchedMountainRobust( excludes, aMountain ):
      result.append( aMountain )
  return result


if __name__=="__main__":
  parser = argparse.ArgumentParser(description='Parse command line options.')
  parser.add_argument('args', nargs='*', help='mountain name such as 富士山')
  parser.add_argument('-c', '--compare', action='store_true', help='compare mountains per day')
  parser.add_argument('-s', '--score', action='store', help='specify score key e.g. 登山_明日, 天気_今日, etc.')
  parser.add_argument('-t', '--time', action='store', default='0-24', help='specify time range e.g. 6-15')
  parser.add_argument('-d', '--date', action='store', default='', help='specify date e.g. 2/14')
  parser.add_argument('-e', '--exclude', action='store', default='', help='specify excluding mountain list file e.g. climbedMountains.lst')
  parser.add_argument('-i', '--include', action='store', default='', help='specify including mountain list file e.g. climbedMountains.lst')
  parser.add_argument('-a', '--acceptClimbRates', action='store', default='A,B,C', help='specify acceptable climbRate conditions default:A,B,C')

  args = parser.parse_args()

  mountains = mountainsIncludeExcludeFromFile( args.args, args.exclude, args.include )
  mountains = set( mountains )

  if len(mountains) == 0:
    parser.print_help()
    exit(-1)

  mountainWeathers={}
  for aMountain in mountains:
    mountainKeys = getMountainKeys(aMountain)
    for theMountain in mountainKeys:
      mountainWeathers[ theMountain ] = addingScoringMountain( getWeather( mountainDic[theMountain] ), args.score )

  perKeyMaxLengths = get_max_length_per_category(mountainWeathers)
  nonDispKeys = ["url", "score"]
  startTime, endTime = getTimeRange( args.time )

  if False == args.compare:
    dumpPerMountain(mountainWeathers, nonDispKeys, args.date, startTime, endTime, args.acceptClimbRates )
  else:
    dumpPerCategory(mountainWeathers, nonDispKeys, args.date, startTime, endTime, args.acceptClimbRates )
