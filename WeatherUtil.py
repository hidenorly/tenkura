#!/usr/bin/env python3
# coding: utf-8
#   Copyright 2025 hidenorly
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

from selenium import webdriver
import datetime
import os
import re
import datetime
from datetime import timedelta, datetime
import json
import sys
import subprocess
import shlex

try:
    from mountain_weather_dic import mountain_weather_dic
except:
    pass


class ReportUtil:
  @staticmethod
  def get_count(value):
    count_length = 0
    for char in value.encode().decode('utf8'):
      if ord(char) <= 255:
        count_length += 1
      else:
        count_length += 2
    return count_length

  @staticmethod
  def ljust_jp(value, length, pad = " "):
    count_length = ReportUtil.get_count(value)
    return str(value + pad * (length-count_length))[0:length]

  @staticmethod
  def frontPaddingStr(str, length):
    thePaddingLength = length - len(str)
    return " "*thePaddingLength + str

  @staticmethod
  def printKeyArray(key, keyLength, arrayData, padding=" ", lPadding=""):
    key = ReportUtil.ljust_jp(key, keyLength-len(lPadding))
    val = ""
    for aData in arrayData:
      if aData == "":
        aData=padding
      val = val + aData + padding
    print( lPadding + key + ": " + val )


class WebUtil:
  @staticmethod
  def get_web_driver(width=1920, height=1080):
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    tempDriver = webdriver.Chrome(options=options)
    userAgent = tempDriver.execute_script("return navigator.userAgent")
    userAgent = userAgent.replace("headless", "")
    userAgent = userAgent.replace("Headless", "")

    options = webdriver.ChromeOptions()
    options.page_load_strategy = 'eager'
    options.add_argument('--headless')
    options.add_argument(f"user-agent={userAgent}")
    driver = webdriver.Chrome(options=options)
    driver.set_window_size(width, height)

    return driver

class JsonCache:
  DEFAULT_CACHE_BASE_DIR = os.path.expanduser("~")+"/.cache"
  DEFAULT_CACHE_EXPIRE_HOURS = 1 # an hour

  def __init__(self, cacheDir = None, expireHour = None):
    self.cacheBaseDir = cacheDir if cacheDir else JsonCache.DEFAULT_CACHE_BASE_DIR
    self.expireHour = expireHour if expireHour else JsonCache.DEFAULT_CACHE_EXPIRE_HOURS

  def ensureCacheStorage(self):
    if not os.path.exists(self.cacheBaseDir):
      os.makedirs(self.cacheBaseDir)

  def getCacheFilename(self, url):
    result = url
    result = re.sub(r'^https?://', '', url)
    result = re.sub(r'^[a-zA-Z0-9\-_]+\.[a-zA-Z]{2,}', '', result)
    result = re.sub(r'[^a-zA-Z0-9._-]', '_', result)
    result = re.sub(r'\.', '_', result)
    result = re.sub(r'=', '_', result)
    result = re.sub(r'#', '_', result)
    result = result + ".json"
    return result

  def getCachePath(self, url):
    return os.path.join(self.cacheBaseDir, self.getCacheFilename(url))

  def storeToCache(self, url, result):
    self.ensureCacheStorage()
    cachePath = self.getCachePath( url )
    dt_now = datetime.now()
    _result = {
      "lastUpdate":dt_now.strftime("%Y-%m-%d %H:%M:%S"),
      "data": result
    }
    with open(cachePath, 'w', encoding='UTF-8') as f:
      json.dump(_result, f, indent = 4, ensure_ascii=False)
      f.close()

  def isValidCache(self, lastUpdateString):
    result = False
    lastUpdate = datetime.strptime(lastUpdateString, "%Y-%m-%d %H:%M:%S")
    dt_now = datetime.now()
    if dt_now < ( lastUpdate+timedelta(hours=self.expireHour) ):
      result = True

    return result

  def restoreFromCache(self, url):
    result = None
    cachePath = self.getCachePath( url )
    if os.path.exists( cachePath ):
      with open(cachePath, 'r', encoding='UTF-8') as f:
        _result = json.load(f)
        f.close()

      if "lastUpdate" in _result:
        if self.isValidCache( _result["lastUpdate"] ):
          result = _result["data"]

    return result


class ExecUtil:
  @staticmethod
  def _getOpen():
    result = "open"
    if sys.platform.startswith('win'):
      result = "start"
    return result

  @staticmethod
  def open(url):
    exec_cmd = f'{ExecUtil._getOpen()} {shlex.quote(url)}'
    result = subprocess.run(exec_cmd, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8')
    return result


class WeatherConstants:
    def get_weather_desc(icon_url):
      weather_id = icon_url

      pos1 = icon_url.rfind("/")
      pos2 = icon_url.rfind(".")
      if pos1!=-1 and pos2!=-1:
        weather_id = icon_url[pos1+1:pos2]

      if weather_id in WeatherConstants.WEATHER_ID_STRING_MAP:
        icon_url = WeatherConstants.WEATHER_ID_STRING_MAP[weather_id]

      return icon_url

    WEATHER_ID_STRING_MAP = {
        "100": "fine",
        "101": "fine_cloud",
        "102": "fine_rain",
        "103": "fine_rain",
        "104": "fine_snow",
        "105": "fine_snow",
        "106": "fine_rain",
        "107": "fine_rain",
        "108": "fine_rain",
        "110": "fine_cloud",
        "111": "fine_cloud",
        "112": "fine_rain",
        "113": "fine_rain",
        "114": "fine_rain",
        "115": "fine_snow",
        "116": "fine_rain",
        "117": "fine_snow",
        "118": "fine_rain",
        "119": "fine_rain",
        "120": "fine_rain",
        "121": "fine_cloud",
        "122": "fine_rain",
        "123": "fine",
        "124": "fine",
        "125": "fine_rain",
        "126": "fine_rain",
        "127": "fine_rain",
        "128": "fine_rain",
        "129": "fine_rain",
        "130": "fine",
        "131": "fine",
        "132": "fine_cloud",
        "140": "fine_rain",
        "160": "fine_snow",
        "170": "fine_snow",
        "181": "fine_snow",

        "200": "cloud",
        "201": "cloud_fine",
        "202": "cloud_rain",
        "203": "cloud_rain",
        "204": "cloud_snow",
        "205": "cloud_snow",
        "206": "cloud_rain",
        "207": "cloud_rain",
        "208": "cloud_rain",
        "209": "cloud",
        "210": "cloud_fine",
        "211": "cloud_fine",
        "212": "cloud_rain",
        "213": "cloud_rain",
        "214": "cloud_rain",
        "215": "cloud_snow",
        "216": "cloud_snow",
        "217": "cloud_snow",
        "218": "cloud_rain",
        "219": "cloud_rain",
        "220": "cloud_rain",
        "221": "cloud_rain",
        "222": "cloud_rain",
        "223": "cloud_fine",
        "224": "cloud_rain",
        "225": "cloud_rain",
        "226": "cloud_rain",
        "227": "cloud_rain",
        "228": "cloud_snow",
        "229": "cloud_snow",
        "230": "cloud_snow",
        "231": "cloud",
        "240": "cloud_rain",
        "250": "cloud_snow",
        "260": "cloud_snow",
        "270": "cloud_snow",
        "281": "cloud_snow",

        "300": "rain",
        "301": "rain_fine",
        "302": "rain",
        "303": "rain_snow",
        "304": "rain",
        "306": "rain",
        "308": "rain",
        "309": "rain_snow",
        "311": "rain_fine",
        "313": "rain_cloud",
        "314": "rain_snow",
        "315": "rain_snow",
        "316": "rain_fine",
        "317": "rain_cloud",
        "320": "rain_fine",
        "321": "rain_cloud",
        "322": "rain_snow",
        "323": "rain_fine",
        "324": "rain_fine",
        "325": "rain_fine",
        "326": "rain_snow",
        "327": "rain_snow",
        "328": "rain",
        "329": "rain",
        "340": "snow",
        "350": "rain",
        "361": "snow_fine",
        "371": "snow_cloud",

        "400": "snow",
        "401": "snow_fine",
        "402": "snow_cloud",
        "403": "snow_rain",
        "405": "snow",
        "406": "snow",
        "407": "snow",
        "409": "snow_rain",
        "411": "snow_fine",
        "420": "snow_fine",
        "421": "snow_cloud",
        "422": "snow_rain",
        "423": "snow_rain",
        "424": "snow_rain",
        "425": "snow",
        "426": "snow",
        "427": "snow",
        "430": "snow",
        "450": "snow",

        "500": "fine",
        "550": "fine",

        "600": "fine",
        "650": "rain",

        "800": "cloud_thunder",
        "850": "rain(heavy)",
        "851": "rain(heavy)_fine",
        "852": "rain(heavy)_cloud",
        "853": "rain(heavy)_rain",
        "853": "rain(heavy)_snow",
        "854": "rain(heavy)_fine",

        "950": "snow",
        "951": "snow_fine",
        "952": "snow_cloud",
        "953": "snow_rain",
        "954": "snow",
    }

class WeatherUtils:
    def isMatchedDate(the_day, target_YYMMDDs):
        if not target_YYMMDDs or target_YYMMDDs == ['']:
            return True
        the_day = int(the_day)
        for targetYYMMDD in target_YYMMDDs:
            pos = targetYYMMDD.rfind("/")
            if pos!=-1:
                day = int(targetYYMMDD[pos+1:])
                if the_day == day:
                    return True
        return False

    def get_weather_url_info_by_name(mountain_name):
        try:
          for url, infos in mountain_weather_dic.items():
              if mountain_name in infos.keys():
                  return url, infos[mountain_name]
              else:
                  for candidate_mountain_name in infos.keys():
                      if candidate_mountain_name.find(mountain_name)!=-1:
                          return url, infos[candidate_mountain_name]
        except:
          pass
        return None, None

    def get_listurl_url_by_name(mountain_names):
        urls = set()
        results = {}
        for mountain_name in mountain_names:
            url, info = WeatherUtils.get_weather_url_info_by_name(mountain_name)
            if url!=None:
                urls.add(url)
            if info!=None:
                results[mountain_name] = info
        return urls, results

    def is_matched_mountain(mountain_name, mountain_names):
        if mountain_name in mountain_names:
            return True
        else:
            for a_mountain_name in mountain_names:
                if mountain_name.find(a_mountain_name)!=-1:
                    return True
        return False

    def is_matched_weather(weather, acceptableWeatherConditions):
        if weather in acceptableWeatherConditions:
            return acceptableWeatherConditions[weather]
        return True
