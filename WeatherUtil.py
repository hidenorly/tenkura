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
    return value + pad * (length-count_length)

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
