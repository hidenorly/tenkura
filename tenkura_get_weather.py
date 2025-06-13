#!/usr/bin/env python3
# coding: utf-8
#   Copyright 2021, 2022, 2023, 2024,2025 hidenorly
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
import json
import time

from bs4 import BeautifulSoup

import mountainDic
import mountainInfoDic
from WeatherUtil import ExecUtil, ReportUtil

class MountainDicUtil:
  mountainDic = mountainDic.getMountainDic()

  @staticmethod
  def getMountainKeys(key):
    result = set()
    for dicKey, value in MountainDicUtil.mountainDic.items():
      if dicKey.startswith(key):
        result.add( dicKey )
    return result

  @staticmethod
  def getUrl(mountainKey):
    result = ""
    if mountainKey in MountainDicUtil.mountainDic:
      result = MountainDicUtil.mountainDic[ mountainKey ]
    return result


class WeatherCache:
  CACHE_BASE_DIR = os.path.expanduser("~")+"/.cache/weather"
  CACHE_EXPIRE_HOURS = 3 # 3 hour

  @staticmethod
  def ensureCacheStorage():
    if not os.path.exists(WeatherCache.CACHE_BASE_DIR):
      os.makedirs(WeatherCache.CACHE_BASE_DIR)

  @staticmethod
  def getCacheFilename(url):
    result = url
    pos = str(url).rfind("/")
    if pos!=-1:
      result = url[pos+1:len(url)]
    return result

  @staticmethod
  def getCachePath(url):
    return WeatherCache.CACHE_BASE_DIR+"/"+WeatherCache.getCacheFilename(url)

  @staticmethod
  def storeToCache(url, result):
    WeatherCache.ensureCacheStorage()
    cachePath = WeatherCache.getCachePath( url )
    dt_now = datetime.datetime.now()
    _result = {}
    _result["body"] = result
    _result["lastUpdate"] = dt_now.strftime("%Y-%m-%d %H:%M:%S")

    with open(cachePath, 'w', encoding='UTF-8') as f:
      json.dump(_result, f, indent = 4, ensure_ascii=False)
      f.close()


  @staticmethod
  def isValidCache( lastUpdateString ):
    result = False
    lastUpdate = datetime.datetime.strptime(lastUpdateString, "%Y-%m-%d %H:%M:%S")
    dt_now = datetime.datetime.now()
    if dt_now < ( lastUpdate+datetime.timedelta(hours=WeatherCache.CACHE_EXPIRE_HOURS) ):
      # the following is tenkura specific since the forecast is updated every 3 hours.
      if int(dt_now.hour / WeatherCache.CACHE_EXPIRE_HOURS) == int(lastUpdate.hour / WeatherCache.CACHE_EXPIRE_HOURS):
        result = True

    return result

  @staticmethod
  def restoreFromCache(cachePath):
    result = None
    with open(cachePath, 'r', encoding='UTF-8') as f:
      _result = json.load(f)

    if "lastUpdate" in _result:
      if WeatherCache.isValidCache( _result["lastUpdate"] ):
        del _result["lastUpdate"]
        if "body" in _result:
          result = _result["body"]

    return result

  @staticmethod
  def getCachedWeather(url):
    result = None
    cachePath = WeatherCache.getCachePath( url )
    if os.path.exists( cachePath ):
      result = WeatherCache.restoreFromCache( cachePath )

    return result

  @staticmethod
  def getRawWeather(url):
    result = []
    theDay = []
    result.append( url )

    tables = None
    try:
      res = requests.get(url)
      soup = BeautifulSoup(res.text, 'html.parser')
      tables = soup.find_all("table")#, class_='only-pc')
    except:
      print(f'error at {url}')

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
                    climbScore = TenkuraUtil.getClimbScore(theUrl)
                    if None != climbScore :
                      theDay.append(climbScore)
                      TenkuraUtil.maintainResult(result, "登山")
                  elif imgAlt == "天気":
                    weatherScore = TenkuraUtil.getWeatherScore(theUrl)
                    if None != weatherScore :
                      theDay.append(weatherScore)
                      TenkuraUtil.maintainResult(result, "天気")
        if len(theDay) != 0:
          result.append( theDay )

    return result

  @staticmethod
  def getWeather(url, forceReload = False):
    result = WeatherCache.getCachedWeather( url )
    if result == None or forceReload:
      result = WeatherCache.getRawWeather( url )
      WeatherCache.storeToCache( url, result )
    return result


class TenkuraUtil:
  @staticmethod
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

  @staticmethod
  def getWeatherString(weatherStatus):
    result = ""
    if weatherStatus in TenkuraUtil.weatherStatusDic:
      result = TenkuraUtil.weatherStatusDic[weatherStatus]
    return result

  @staticmethod
  def getWeatherScore(url):
    result = None
    if url.find("/tenkim/")!=-1 and url.endswith(".gif"):
      weatherIcon = url[url.rfind("/")+2:len(url)-4]
      result = str.ljust(TenkuraUtil.getWeatherString(weatherIcon), 10)

    return result

  @staticmethod
  def getFormatedKeyString(text):
    result = text
    result = result.replace("週　間　予　報", "週間予報")
    result = result.replace("明 日", "明日")
    result = result.replace("あさって", "明後日")
    result = result.replace("  ", ":")
    return result

  @staticmethod
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
          text = TenkuraUtil.getFormatedKeyString(text)
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

  @staticmethod
  def maintainResult(result, separator):
    theValue = result[len(result)-1]
    if isinstance(theValue, str) and theValue.startswith("_"):
      result[len(result)-1] = separator + theValue

  @staticmethod
  def getWeather(url, foreceReload = False):
    result = WeatherCache.getWeather(url, foreceReload)
    return TenkuraUtil.filterWeather(result)





class TenkuraScoreUtil:
  @staticmethod
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

  @staticmethod
  def addingScoringMountain( mountain, scoreKey ):
    if scoreKey:
      score = 0
      for key,value in mountain.items():
        if key.find(scoreKey)!=-1:
          if isinstance(value, list):
            for aData in value:
              score = score + TenkuraScoreUtil.getRecommendationScore(aData)
      mountain["score"] = score
    return mountain


class MountainDetailUtil:
  mountainInfoDic = mountainInfoDic.getMountainInfoDic()

  @staticmethod
  def getMountainDetailInfo(mountainName):
    result = None

    if( mountainName in MountainDetailUtil.mountainInfoDic):
      result = MountainDetailUtil.mountainInfoDic[mountainName]
    else:
      pos = mountainName.find("_")
      if pos != -1:
        mountainName = mountainName[0 : pos - 1 ]
      pos = mountainName.find("（")
      if pos != -1:
        mountainName = mountainName[0 : pos - 1 ]
      for aMountainName, anInfo in MountainDetailUtil.mountainInfoDic.items():
        if aMountainName.find( mountainName )!=-1:
          result = anInfo
          break

    return result

  @staticmethod
  def printMountainDetailInfo(mountainName):
    info = MountainDetailUtil.getMountainDetailInfo( mountainName )
    if info!=None:
      print( ReportUtil.ljust_jp(" altitude", 20) + ": " + info["altitude"] )
      print( ReportUtil.ljust_jp(" area", 20) + ": " + info["area"] )
      print( ReportUtil.ljust_jp(" difficulty", 20) + ": " + info["difficulty"] )
      print( ReportUtil.ljust_jp(" fitnessLevel", 20) + ": " + info["fitnessLevel"] )
      print( ReportUtil.ljust_jp(" type", 20) + ": " + info["type"] )
      print( "" )


class TenkuraStandardizedUtil:
  @staticmethod
  def getStandardizedKey(key):
    result = key
    pos = key.find(":")
    if pos!=-1:
      result = key[pos+1:len(key)]
    if key.endswith("週間予報"):
      result = "weekly"
    return result

  @staticmethod
  def getHashArrayMaxLength(hashArrayData):
    result = 0
    if hasattr(hashArrayData, "__iter__"):
      for key, anArrayData in hashArrayData.items():
        if hasattr(anArrayData, "__iter__"):
          nLen = len(anArrayData)
          if result < nLen:
            result = nLen

    return result

  @staticmethod
  def getLengthEnsuredArrayWithFrontPadding(hashArrayData):
    nEnsuredSize = TenkuraStandardizedUtil.getHashArrayMaxLength(hashArrayData)
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

  @staticmethod
  def isClimbRate(climbData):
    result = False

    if hasattr(climbData, "__iter__"):
      result = True
      for aData in climbData:
        if not (aData=="A" or aData=="B" or aData=="C"):
          result = False
          break

    return result

  @staticmethod
  def getStandardizedMountainData(weatherData):
    result = {}
    result["climbRate"]={}
    result["climbRate_weekly"]={}
    result["weather"]={}
    result["weather_weekly"]={}
    result["misc"]={}

    for key, aData in weatherData.items():
      rootKey = "weather"
      if TenkuraStandardizedUtil.isClimbRate(aData):
        rootKey = "climbRate"
      key = TenkuraStandardizedUtil.getStandardizedKey(key)

      if key=="weekly":
        if TenkuraStandardizedUtil.isClimbRate(aData):
          rootKey = "climbRate_weekly"
        else:
          rootKey = "weather_weekly"
      elif key=="url":
        rootKey = "misc"
      elif key=="score":
        rootKey = "misc"
      result[rootKey][key] = aData


    result["climbRate"] = TenkuraStandardizedUtil.getLengthEnsuredArrayWithFrontPadding(result["climbRate"])
    result["weather"] = TenkuraStandardizedUtil.getLengthEnsuredArrayWithFrontPadding(result["weather"])

    return result


class MathUtil:
  @staticmethod
  def isRobustNumeric(data):
    if data is not None:
      try:
        float(data)
      except ValueError:
        return False
      return True
    else:
      return False


class TenkuraFilterUtil:
  @staticmethod
  def getAcceptableWeatherConditions(excludingWeathers):
    result = {}

    for anId, aWeather in TenkuraUtil.weatherStatusDic.items():
      isOk = True
      for anExclude in excludingWeathers:
        if anExclude and ( anExclude.find( aWeather )!=-1 or aWeather.find( anExclude )!=-1 ):
          isOk = False
          break
      result[ aWeather ] = isOk

    return result

  @staticmethod
  def getTimeIndex(timeHH):
    result = int(timeHH / 3)
    result = result % 9
    return result

  @staticmethod
  def getTimeRangeFilter(climbRates, startTime, endTime):
    startIndex = TenkuraFilterUtil.getTimeIndex(startTime)
    endIndex = TenkuraFilterUtil.getTimeIndex(endTime)
    if startIndex > endIndex:
      startIndex, endIndex = endIndex, startIndex
    if len(climbRates) == 8:
      climbRates = climbRates[startIndex:endIndex]
    return climbRates

  @staticmethod
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

  @staticmethod
  def getYYMMDD(yymmdd):
    yy = "0"
    mm = "0"
    dd = "0"

    pos1 = yymmdd.find("/")
    pos2 = yymmdd.rfind("/")
    if pos1!=-1 and pos2!=-1:
      if pos1!=pos2:
        # found yy
        yy = yymmdd[0:pos1]
        mm = yymmdd[pos1+1:pos2]
        dd = yymmdd[pos2+1:len(yymmdd)]
      else:
        mm = yymmdd[0:pos2]
        dd = yymmdd[pos2+1:len(yymmdd)]
    else:
      dd = yymmdd

    return int(yy), int(mm), int(dd)


  @staticmethod
  def ensureYearMonth(yymmdd, refYYMMDD = "", isMMDD=False):
    if refYYMMDD=="":
      refYYMMDD = datetime.datetime.now().strftime("%Y/%m/%d")

    yy1, mm1, dd1 = TenkuraFilterUtil.getYYMMDD(yymmdd)
    yy2, mm2, dd2 = TenkuraFilterUtil.getYYMMDD(refYYMMDD)

    if dd1<dd2:
      mm1 = ( mm2 + 1 ) % 13
      if mm1 == 0:
        mm1 = mm1 + 1

    if mm1 == 0:
      mm1 = mm2

    if yy1<yy2:

      yy1 = yy2
      if mm1<mm2:
        yy1 = yy1 + 1

    result = "{:04d}".format(yy1)+"/"+"{:02d}".format(mm1)+"/"+"{:02d}".format(dd1)
    if isMMDD:
      result = "{:02d}".format(mm1)+"/"+"{:02d}".format(dd1)
    return result


  @staticmethod
  def getListOfRangedDates(fromDay, toDay, isMMDD=False):
    result = []

    fromDay = TenkuraFilterUtil.ensureYearMonth( fromDay, "" )
    toDay = TenkuraFilterUtil.ensureYearMonth( toDay, fromDay )

    fromDay = TenkuraFilterUtil.getDateTimeFromYYMMDD( fromDay )
    toDay = TenkuraFilterUtil.getDateTimeFromYYMMDD( toDay )

    theDay = fromDay
    dateFormat = "%Y/%m/%d"
    if isMMDD:
      dateFormat = "%m/%d"
    while theDay <= toDay:
      result.append( theDay.strftime( dateFormat ) )
      theDay = theDay + datetime.timedelta(days=1)

    return result

  @staticmethod
  def getListOfDates(dateOptionString):
    result = []

    commaValues = dateOptionString.split(",")
    for aValue in commaValues:
      aValue = aValue.strip()
      rangedValue = aValue.split("-")
      if len( rangedValue ) == 2:
        result.extend( TenkuraFilterUtil.getListOfRangedDates( rangedValue[0].strip(), rangedValue[1].strip() ) )
      else:
        if not aValue:
          result.append( aValue )
        else:
          result.append( TenkuraFilterUtil.ensureYearMonth( aValue, "", False ) )

    if len(result) == 0:
      result = [ dateOptionString ]

    return result

  @staticmethod
  def isMatchedDate(key, targetDateMMDDs):
    result = False
    for targetDateMMDD in targetDateMMDDs:
      if targetDateMMDD=="" or TenkuraFilterUtil.getDateTimeFromYYMMDD(key) == TenkuraFilterUtil.getDateTimeFromYYMMDD(targetDateMMDD):
        result = True
        break

    return result

  @staticmethod
  def getCleanedDateKey(dateKey):
    pos = dateKey.rfind("(")
    if pos!=-1:
      dateKey = dateKey[0:pos]
    return dateKey

  @staticmethod
  def getMaxDateYYMMDD(climbRates):
    result = ""
    score = TenkuraFilterUtil.getDateTimeFromYYMMDD("")
    foundKey = ""
    for key, arrayData in climbRates.items():
      currentScore = TenkuraFilterUtil.getDateTimeFromYYMMDD(key)
      if currentScore > score:
        score = currentScore
        foundKey = key

    if foundKey:
        maxDate = TenkuraFilterUtil.getDateTimeFromYYMMDD( foundKey )
        result = maxDate.strftime('%Y/%m/%d')

    return result

  @staticmethod
  def isYearIncluded(yymmdd):
    yymmdd = str(yymmdd)
    pos1 = yymmdd.find("/")
    pos2 = yymmdd.rfind("/")
    result = False
    if pos1!=-1 and pos2!=-1 and pos1!=pos2:
      result = True
    return result

  @staticmethod
  def getDateTimeFromYYMMDD(yymmdd):
    yymmdd = str(yymmdd)
    yymmdd = TenkuraFilterUtil.getCleanedDateKey(yymmdd)
    if yymmdd=="":
      yymmdd="1/1"

    if not TenkuraFilterUtil.isYearIncluded(yymmdd):
      yymmdd = datetime.datetime.now().strftime("%Y") + "/" + yymmdd

    return datetime.datetime.strptime(yymmdd, "%Y/%m/%d")

  @staticmethod
  def getDateRangeFilterForWeek(weeklyArrayData, startDateTime, targetDateTime):
    result = []
    currentDateTime = startDateTime
    for aData in weeklyArrayData:
      if currentDateTime == targetDateTime:
        result.append( aData )
      currentDateTime = currentDateTime + datetime.timedelta(days=1)

    return result


  @staticmethod
  def getWeekEndDates(startDateTime):
    result = []
    currentDateTime = startDateTime
    theRange = 8 if currentDateTime.weekday() == 6 else 7

    for i in range(theRange):
      weekDay = currentDateTime.weekday()
      if weekDay == 5 or weekDay == 6:
        result.append( currentDateTime )
      currentDateTime = currentDateTime + datetime.timedelta(days=1)

    return result

  @staticmethod
  def getWeekEndYYMMDD(startDateTime, isMMDD=True):
    weekendDateTimes = TenkuraFilterUtil.getWeekEndDates(startDateTime)
    result = []
    dateFormat = '%Y/%m/%d'
    if isMMDD:
      dateFormat = '%m/%d'
    for theDateTime in weekendDateTimes:
      result.append( TenkuraFilterUtil.ensureYearMonth(theDateTime.strftime( dateFormat ), "", isMMDD ))

    return result

  @staticmethod
  def isAcceptableClimbRateRange( arrayData, acceptableClimbRates ):
    result = True
    acceptableClimbRates = acceptableClimbRates.split(",")
    for aData in arrayData:
      if aData!="":
        isOk = False
        for anAcceptableRate in acceptableClimbRates:
          if aData == anAcceptableRate:
            isOk = True
            break
        if not isOk:
          result = False
          break

    return result

  @staticmethod
  def isAcceptableWeatherConditions( arrayData, acceptableWeatherConditions ):
    result = True
    for aData in arrayData:
      aData = aData.strip()
      if aData!="":
        result = acceptableWeatherConditions[ aData ]
        if result == False:
          break

    return result

  @staticmethod
  def getAcceptableClimbRateRangesForWeek( weeklyData, acceptableClimbRates ):
    result = []
    for aData in weeklyData:
      found = False
      for anAcceptableClimbRate in acceptableClimbRates:
        if aData == anAcceptableClimbRate:
          result.append( aData )
          found = True
          break
      if not found:
        result.append("-")

    foundCount = 0
    for aData in result:
      if aData != "-":
        foundCount = foundCount + 1
    if foundCount==0:
      result = []

    return result

  @staticmethod
  def getDispDays(weeklyDates):
    weeklyDays = ""
    lastMonth = ""

    for aDay in weeklyDates:
      theDay = aDay
      if theDay.startswith("0"):
        theDay = theDay[1:len(theDay)]
      posMonth = theDay.find("/")
      if posMonth!=-1:
        if lastMonth == theDay[0:posMonth]:
          theDay = theDay[posMonth+1:len(theDay)]
        else:
          lastMonth = theDay[0:posMonth]
      weeklyDays = weeklyDays + "," + theDay
    if weeklyDays.startswith(","):
      weeklyDays = weeklyDays[1:len(weeklyDays)]

    return weeklyDays

  @staticmethod
  def getFilteredMountainInfo(stadndarizedData, targetDateMMDDs, startTime, endTime, acceptableClimbRates, acceptableWeatherConditions):
    result = {}
    result["climbRate"] = {}
    result["climbRate_weekly"] = {}
    result["weather"] = {}
    result["weather_weekly"] = {}
    result["misc"] = stadndarizedData["misc"]
    weeklyDates = []

    # per day : climb rate & weather rate
    for key, climbData in stadndarizedData["climbRate"].items():
      if TenkuraFilterUtil.isMatchedDate( key, targetDateMMDDs ):
        climbData = TenkuraFilterUtil.getTimeRangeFilter( climbData, startTime, endTime )
        if TenkuraFilterUtil.isAcceptableClimbRateRange( climbData, acceptableClimbRates ):
          if key in stadndarizedData["weather"]:
            weatherData = stadndarizedData["weather"][key]
            weatherData = TenkuraFilterUtil.getTimeRangeFilter( weatherData, startTime, endTime )
            if TenkuraFilterUtil.isAcceptableWeatherConditions( weatherData, acceptableWeatherConditions ):
              result["weather"][key] = weatherData
              result["climbRate"][key] = climbData

    # weekly climb rate
    climbRateDayMax = TenkuraFilterUtil.getMaxDateYYMMDD( stadndarizedData["climbRate"] )
    if climbRateDayMax=="":
      climbRateDayMax = datetime.datetime.now().strftime('%Y/%m/%d')
    if climbRateDayMax!="":
      climbRateDayMax_dateTime = TenkuraFilterUtil.getDateTimeFromYYMMDD( climbRateDayMax )
      weekStart_dateTime = climbRateDayMax_dateTime + datetime.timedelta(days=1)

      if ( "climbRate_weekly" in stadndarizedData ) and ( "weekly" in stadndarizedData["climbRate_weekly"] ):
        weeklyData = stadndarizedData["climbRate_weekly"]["weekly"]
        if str(targetDateMMDDs)!="":
          tmp = []
          for targetDateMMDD in targetDateMMDDs:
            aMatchedWeek = TenkuraFilterUtil.getDateRangeFilterForWeek( weeklyData, weekStart_dateTime, TenkuraFilterUtil.getDateTimeFromYYMMDD(targetDateMMDD) )
            tmp.extend( aMatchedWeek )
            if len( aMatchedWeek )!=0:
              weeklyDates.append( targetDateMMDD )
          weeklyData = tmp
        if len( weeklyData )!=0:
          filteredWeeklyClimbRates = TenkuraFilterUtil.getAcceptableClimbRateRangesForWeek( weeklyData, acceptableClimbRates )
          if len(filteredWeeklyClimbRates)!=0:
            result["climbRate_weekly"]["weekly"] = filteredWeeklyClimbRates

    weeklyDays = TenkuraFilterUtil.getDispDays( weeklyDates )

    return result, weeklyDays

  @staticmethod
  def dateSortUtil(dateString):
    dateString = TenkuraFilterUtil.ensureYearMonth(dateString)
    year, month, day = TenkuraFilterUtil.getYYMMDD(dateString)
    return int(year)*403+ int(month) * 31 + int(day)



class TenkuraReportUtil:
  @staticmethod
  def dumpPerMountain(mountainWeathers, disablePrint, noSupplementalInfo, replaceKeys, noUrl):
    result = set()

    for aMountain, stadndarizedData in mountainWeathers.items():
      # print detail climb rate
      found = False
      for key, arrayData in stadndarizedData["climbRate"].items():
        if not found:
          found = True
          if not disablePrint:
            print( aMountain + " : " )
        if not disablePrint:
          ReportUtil.printKeyArray( key, 20, arrayData, lPadding=" ")
        result.add( aMountain )

      # print weekly climb rate
      if ( "climbRate_weekly" in stadndarizedData ) and ( "weekly" in stadndarizedData["climbRate_weekly"] ):
        weeklyData = stadndarizedData["climbRate_weekly"]["weekly"]
        if not found:
          if not disablePrint:
            print( aMountain + " : " )
          found = True
        if not disablePrint:
          theDispKey = "weekly"
          if "weekly" in replaceKeys:
            theDispKey = replaceKeys["weekly"]
          ReportUtil.printKeyArray( theDispKey, 20, weeklyData, lPadding=" ")
        result.add( aMountain )

      if found and not disablePrint:
        # print detail weather rate
        for key, arrayData in stadndarizedData["weather"].items():
          ReportUtil.printKeyArray( key, 20, arrayData, lPadding=" ")

        # print misc.
        if "misc" in stadndarizedData:
          if "url" in stadndarizedData["misc"] and not noUrl:
            ReportUtil.printKeyArray( "url", 20, stadndarizedData["misc"]["url"], "", lPadding=" " )
          if "score" in stadndarizedData["misc"]:
            print( ReportUtil.ljust_jp(" score", 20) + ": " + str(stadndarizedData["misc"]["score"]) )

        # print mountain detail
        if not noSupplementalInfo:
          MountainDetailUtil.printMountainDetailInfo( aMountain )

        print("")

    return result

  @staticmethod
  def dumpPerCategory(standarizedData, noSupplementalInfo, nonDispKeys, replaceKeys, targetDateMMDD, noUrl):
    result = set()
    dispKeys = {}
    dispCategory = {}
    for aMountain, aStadndarizedData in standarizedData.items():
      for key, value in aStadndarizedData.items():
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
                arrayData = aStandarizedData[aCategoryKey][aDispKey]
                if found == False:
                  print( "" )
                  theDispKey = aDispKey
                  if aDispKey in replaceKeys:
                    theDispKey = replaceKeys[aDispKey]
                  print( aCategoryKey + ":" + theDispKey )
                  found = True
                ReportUtil.printKeyArray( aMountainName, 20, arrayData, lPadding=" " )
                displayedMountains[aMountainName] = True
                result.add( aMountainName )
                foundData = True

    # fallback
    if foundData==False:
      for aMountainName, aStandarizedData in standarizedData.items():
        if ( "climbRate_weekly" in aStandarizedData ) and ( "weekly" in aStandarizedData["climbRate_weekly"] ):
          weeklyData = aStandarizedData["climbRate_weekly"]["weekly"]
          if len( weeklyData )!=0:
            if foundData == False:
              print( "climbRate_weekly:"+targetDateMMDD )
              foundData = True
            ReportUtil.printKeyArray( aMountainName, 20, weeklyData, lPadding=" ")
            displayedMountains[aMountainName] = True
            result.add( aMountainName )

    if foundData:
      # display detail information
      print( "" )
      for aDispKey in nonDispKeys:
        if (noUrl and aDispKey!="url") or not noUrl:
          print(aDispKey+":")
          for aMountainName, flag in displayedMountains.items():
            theWeather = mountainWeathers[aMountainName]
            if "misc" in theWeather:
              theWeather = theWeather["misc"]
            if aDispKey in theWeather:
              print( " " + ReportUtil.ljust_jp(aMountainName, 19) + ": " + str( theWeather[aDispKey] ) )
            if aDispKey == "url" and not noSupplementalInfo:
              MountainDetailUtil.printMountainDetailInfo( aMountainName )
          print( "" )

    return result

class MountainFilterUtil:
  @staticmethod
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

  @staticmethod
  def isMatchedMountainRobust(arrayData, search):
    result = False
    for aData in arrayData:
      if aData.startswith(search) or search.startswith(aData):
        result = True
        break
    return result

  @staticmethod
  def getSetOfCsvs( csvFiles ):
    result = set()
    csvFiles = csvFiles.split(",")
    for aCsvFile in csvFiles:
      aCsvFile = os.path.expanduser( aCsvFile )
      theSet = set( itertools.chain.from_iterable( MountainFilterUtil.openCsv( aCsvFile ) ) )
      result = result.union( theSet )
    return result

  @staticmethod
  def mountainsIncludeExcludeFromFile( mountains, excludeFile, includeFile ):
    result = set()
    includes = set()
    excludes = set()
    for anExclude in excludeFile:
      excludes =  excludes | MountainFilterUtil.getSetOfCsvs( anExclude )
    for anInclude in includeFile:
      includes = includes | MountainFilterUtil.getSetOfCsvs( anInclude )
    for aMountain in includes:
      mountains.add( aMountain )
    for aMountain in mountains:
      if not MountainFilterUtil.isMatchedMountainRobust( excludes, aMountain ):
        result.add( aMountain )
    return result




if __name__=="__main__":
  parser = argparse.ArgumentParser(description='Parse command line options.')
  parser.add_argument('args', nargs='*', help='mountain name such as 富士山')
  parser.add_argument('-c', '--compare', action='store_true', help='compare mountains per day')
  parser.add_argument('-s', '--score', action='store', help='specify score key e.g. 登山_明日, 天気_今日, etc.')
  parser.add_argument('-t', '--time', action='store', default='0-24', help='specify time range e.g. 6-15')
  parser.add_argument('-d', '--date', action='store', default='', help='specify date e.g. 2/14,2/16-2/17')
  parser.add_argument('-dw', '--dateweekend', action='store_true', help='specify if weekend (Saturday and Sunday)')
  parser.add_argument('-e', '--exclude', action='append', default=[], help='specify excluding mountain list file e.g. climbedMountains.lst')
  parser.add_argument('-i', '--include', action='append', default=[], help='specify including mountain list file e.g. climbedMountains.lst')
  parser.add_argument('-a', '--acceptClimbRates', action='store', default='A,B,C', help='specify acceptable climbRate conditions default:A,B,C')
  parser.add_argument('-w', '--excludeWeatherConditions', action='store', default='', help='specify excluding weather conditions e.g. rain,thunder default is none then all weathers are ok)')
  parser.add_argument('-nn', '--noDetails', action='store_true', default=False, help='specify if you want to output mountain name only')
  parser.add_argument('-ns', '--noSupplementalInfo', action='store_true', default=False, help='specify if you want to output mountain name only')
  parser.add_argument('-nu', '--noUrl', action='store_true', default=False, help='specify if you want to disable tenkura url output')
  parser.add_argument('-m', '--mountainList', action='store_true', default=False, help='specify if you want to output mountain name list')
  parser.add_argument('-r', '--renew', action='store_true', default=False, help='get latest data although cache exists')
  parser.add_argument('-o', '--openUrl', action='store_true', default=False, help='specify if you want to open the url')

  args = parser.parse_args()

  mountains = MountainFilterUtil.mountainsIncludeExcludeFromFile( set(args.args), args.exclude, args.include )
  acceptableWeatherConditions = TenkuraFilterUtil.getAcceptableWeatherConditions( args.excludeWeatherConditions.split(",") )

  if len(mountains) == 0:
    parser.print_help()
    exit(-1)

  mountainList = args.mountainList | args.noDetails
  startTime, endTime = TenkuraFilterUtil.getTimeRange( args.time )

  specifiedDate = TenkuraFilterUtil.getListOfDates( args.date )
  if args.dateweekend:
    weekEndDates = TenkuraFilterUtil.getWeekEndYYMMDD( datetime.datetime.now(), False )
    specifiedDate.extend(weekEndDates)
    specifiedDate = list(set(filter(None,specifiedDate)))
    specifiedDate.sort(key=TenkuraFilterUtil.dateSortUtil)

  # ensure MM/DD for display
  result = []
  for aDay in specifiedDate:
    if aDay:
      result.append( TenkuraFilterUtil.ensureYearMonth(aDay, "", True) )
    else:
      result.append( aDay )
  specifiedDate = result

  mountainWeathers={}
  replaceDispKeys = {}
  replaceDispKeys["weekly"] = ""
  for aMountain in mountains:
    mountainKeys = MountainDicUtil.getMountainKeys(aMountain)
    for theMountain in mountainKeys:
      theWeather = TenkuraUtil.getWeather( MountainDicUtil.getUrl( theMountain ), args.renew )
      theWeather = TenkuraScoreUtil.addingScoringMountain( theWeather, args.score )
      stadndarizedData = TenkuraStandardizedUtil.getStandardizedMountainData(theWeather)
      filteredMountainWeathers, weeklyDays = TenkuraFilterUtil.getFilteredMountainInfo( stadndarizedData, specifiedDate, startTime, endTime, args.acceptClimbRates, acceptableWeatherConditions )
      if len(filteredMountainWeathers)!=0:
        mountainWeathers[ theMountain ] = filteredMountainWeathers
        if len(weeklyDays)>len(replaceDispKeys["weekly"]):
          replaceDispKeys["weekly"] = weeklyDays

  nonDispKeys = ["url", "score"]

  if False == args.compare or args.noDetails:
    mountains = TenkuraReportUtil.dumpPerMountain(mountainWeathers, args.noDetails, args.noSupplementalInfo, replaceDispKeys, args.noUrl )
  else:
    mountains = TenkuraReportUtil.dumpPerCategory(mountainWeathers, args.noSupplementalInfo, nonDispKeys, replaceDispKeys, str(specifiedDate), args.noUrl )

  if mountainList:
    for aMountain in mountains:
      print( aMountain, end = " " )
    print( "" )

  if args.openUrl:
    n = 0
    for key, info in mountainWeathers.items():
      if key in mountains and "misc" in info:
        if "url" in info["misc"]:
          n = n + 1
          if n>2:
            time.sleep(0.5)
          url = info["misc"]["url"]
          ExecUtil.open(url)

