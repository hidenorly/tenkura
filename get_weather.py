#!/usr/bin/env python3
# coding: utf-8
#   Copyright 2024, 2025 hidenorly
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


import os
import datetime
import argparse
import re
import urllib.parse
from urllib.parse import urljoin
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from tenkura_get_weather import TenkuraFilterUtil
from tenkura_get_weather import ReportUtil
from tenkura_get_weather import ExecUtil
from tenkura_get_weather import MountainFilterUtil
from get_mountain_list import MountainList
from WeatherUtil import JsonCache, WebUtil



class Weather:
  URL = "https://www.jma.go.jp/bosai/forecast/"

  def __init__(self, driver = None, renew = False):
    self.cache = JsonCache(os.path.join(JsonCache.DEFAULT_CACHE_BASE_DIR, "weather"), 1)
    self._driver = driver
    self.renew = renew

  def get_weather(self):
    forecast_data = {}

    # try to read from cache
    _result = self.cache.restoreFromCache(self.URL)
    if _result and not self.renew:
      return _result

    # cache is invalid then read with selenium
    if not self._driver:
      self._driver = WebUtil.get_web_driver()

    driver = self._driver
    if driver:
      try:
        driver.get(self.URL)

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'week-table-container'))
        )
        WebDriverWait(driver, 10).until(
          lambda d: d.find_element(By.ID, 'week-table-container').get_attribute('innerHTML').strip() != ""
        )
      except:
        pass

      week_table = driver.find_element(By.ID, 'week-table-container')
      #print(week_table)

      if week_table:
        #week_table_html = week_table.get_attribute('outerHTML')
        #print("Week table HTML:", week_table_html)

        # Extract region blocks
        regions = week_table.find_elements(By.CLASS_NAME, 'contents-wide-table-body')

        if regions:
          for region in regions:
            _forecast_data = {}
            # area
            area_name_elements = region.find_elements(By.CLASS_NAME, 'forecast-area')
            if area_name_elements:
              area_name = None
              for area_name_element in area_name_elements:
                area_name = area_name_element.text.strip()
                if area_name and not area_name in _forecast_data:
                  _forecast_data[area_name] = {}

            # dates
            dates = {}
            _dates = [e.text for e in region.find_elements(By.CLASS_NAME, 'forecast-date')]
            if _dates:
              for _date in _dates:
                if _date and not _date in dates:
                  dates[_date] = True
            dates = dates.keys()

            # weather
            weathers = []
            weather_elements = region.find_elements(By.CLASS_NAME, 'forecast-icon')
            if weather_elements:
              weathers = [e.get_attribute("title") for e in weather_elements]

            # Extract precipitation probability
            precip_probs = []
            precip_prob_elements = region.find_elements(By.XPATH, f".//tr[th[contains(text(), '降水確率')]]")
            if precip_prob_elements:
              _precip_probs = [e.text for e in precip_prob_elements]
              for prob in _precip_probs:
                if prob:
                  precip_probs.append(prob)

            # Extract confidence data
            confidences =[]
            confidence_elements = region.find_elements(By.XPATH, f".//tr[th[contains(text(), '信頼度')]]")
            if confidence_elements:
              _confidences = [e.text for e in confidence_elements]
              for confidence in _confidences:
                if confidence:
                  confidences.append(confidence)

            # Extract temperature
            temperatures = []
            temperature_elements = region.find_elements(By.XPATH, f".//tr[th[div[contains(text(), '最低')]]]")
            if temperature_elements:
              _temperatures = [e.text for e in temperature_elements]
              for temp in _temperatures:
                if temp:
                  temperatures.append(temp)

            num_of_days = len(dates)
            for i, area in enumerate(_forecast_data.keys()):
              for d, day in enumerate(dates):
                day = re.sub(r'.*\n', '', day)
                area_info = _forecast_data[area]
                day_info = area_info[day] = {}
                day_info["天気"] = weathers[i*num_of_days+d]
                day_info["降水確率"] = precip_probs[i].split(" ")[d+1]
                day_info["信頼度"] = confidences[i].split(" ")[d+1]
                day_info["気温"] = temperatures[i].split('\n')[d+1]

            forecast_data.update(_forecast_data)

    if forecast_data:
      self.cache.storeToCache(self.URL, forecast_data)

    return forecast_data

  supported_areas={
    "釧路":["北海道"],
    "旭川":["北海道"],
    "札幌":["北海道"],
    "青森":["青森","東北"],
    "秋田":["秋田","岩手","東北"],
    "仙台":["山形","宮城","東北","上信越"],
    "新潟":["福島県","北・中央アルプス", "北アルプス","東北","上信越"],
    "金沢":["石川","富山","福井","東海・北陸"],
    "東京":["東京都","埼玉","千葉","山梨","神奈川","南関東","奥秩父","関東","奥秩父"],
    "宇都宮":["栃木","群馬", "埼玉", "福島","茨城","南関東","奥秩父","関東","日光","秩父","北関東"],
    "長野":["長野","山梨","静岡","富山","南アルプス","中央アルプス","甲信越","上信越","奥秩父"],
    "名古屋":["愛知","静岡","三重","岐阜"],
    "大阪":["大阪","京都","滋賀","三重","奈良","和歌山","近畿"],
    "高松":["香川","徳島","愛媛","中国・四国"],
    "松江":["島根","鳥取","中国・四国"],
    "広島":["広島","愛媛","岡山","島根","山口","中国・四国","兵庫"],
    "高知":["高知","愛媛","徳島","中国・四国"],
    "福岡":["福岡","大分","熊本","佐賀","長崎","山口","九州"],
    "鹿児島":["鹿児島","宮崎","熊本","九州"],
    "奄美":["沖縄"],
    "那覇":["沖縄"],
    "石垣":["沖縄"],
  }

  def get_nearest_supported_area(area):
    result = set()

    area = area.split("県")[0]

    for supported_area, areas in Weather.supported_areas.items():
      if area in areas:
        result.add(supported_area)

    if not result:
      result = [area]

    return list(result)

  weather_dic={
    "晴":"fine",
    "曇":"cloud",
    "雨":"rain",
  }

  def get_standarized_weathers(weather):
    weathers=set()
    for key, value in Weather.weather_dic.items():
      if key in weather:
        weathers.add(value)
    return weathers

  def is_acceptable_weather(weather, excludeWeatherConditions):
    result = True
    if "天気" in weather:
      standarized_weathers = Weather.get_standarized_weathers(weather["天気"])
      for exclude_condition in excludeWeatherConditions:
        if exclude_condition in standarized_weathers:
          result = False
          break
    return result


def dump_key_value_online(day_info):
    result = ""
    for key,value in day_info.items():
      result=f"{result}   {ReportUtil.ljust_jp(value, max_length[key])}"
    return result


if __name__=="__main__":
  parser = argparse.ArgumentParser(description='Specify expected prefectures or mountain names')
  parser.add_argument('args', nargs='*', help='')
  parser.add_argument('-d', '--date', action='store', default='', help='specify date e.g. 2/14,2/16-2/17')
  parser.add_argument('-dw', '--dateweekend', action='store_true', help='specify if weekend (Saturday and Sunday)')
  parser.add_argument('-c', '--compare', action='store_true', help='compare per day')
  parser.add_argument('-o', '--open', action='store_true', default=False, help='specify if you want to open the page')
  parser.add_argument('-l', '--list', action='store_true', default=False, help='List supported area name')
  parser.add_argument('-r', '--renew', action='store_true', default=False, help='Force to read the site (Ignore cache)')
  parser.add_argument('-w', '--excludeWeatherConditions', action='store', default='', help='specify excluding weather conditions e.g. rain,thunder default is none then all weathers are ok)')
  parser.add_argument('-e', '--exclude', action='append', default=[], help='specify excluding mountain list file e.g. climbedMountains.lst')
  parser.add_argument('-i', '--include', action='append', default=[], help='specify including mountain list file e.g. climbedMountains.lst')

  args = parser.parse_args()
  if args.list:
    print('supported area names are:')
    print(f' {" ".join(Weather.supported_areas.keys())}')
    exit()

  excludeWeatherConditions = args.excludeWeatherConditions.split(",")

  targets = list(MountainFilterUtil.mountainsIncludeExcludeFromFile( set(args.args), args.exclude, args.include ))
  mountain_list = MountainList.get_cached_filtered_mountain_list(targets, True)
  areas = set()
  for mountain in mountain_list:
    for area in mountain["area"].split(" "):
      for supported_area in Weather.get_nearest_supported_area(area):
        areas.add( supported_area )
  targets.extend( list(areas) )
  if areas:
    print(f'area={areas}, targets={targets}')

  specifiedDates = TenkuraFilterUtil.getListOfDates( args.date )
  if args.dateweekend:
    weekEndDates = TenkuraFilterUtil.getWeekEndYYMMDD( datetime.now(), False )
    specifiedDates.extend(weekEndDates)
    specifiedDates = list(set(filter(None,specifiedDates)))
    specifiedDates.sort(key=TenkuraFilterUtil.dateSortUtil)

  weather = Weather(None, args.renew)
  result = weather.get_weather()

  # extract max_length for padding
  max_length={}
  for area, area_info in result.items():
    for day, day_info in area_info.items():
      for key,value in day_info.items():
        if not key in max_length:
          max_length[key]=0
        max_length[key]=max(max_length[key], ReportUtil.get_count(value))

  # dump the result with specified prefectures and dates
  perDayFilteredResult = {}
  for area, area_info in result.items():
    if not targets or area in targets:
      for day, day_info in area_info.items():
        _day = TenkuraFilterUtil.ensureYearMonth(day.split("日")[0])
        if not specifiedDates or (TenkuraFilterUtil.isMatchedDate(_day, specifiedDates)):
          if not _day in perDayFilteredResult:
            perDayFilteredResult[_day] = {}
          if Weather.is_acceptable_weather(day_info, excludeWeatherConditions):
            perDayFilteredResult[_day][area] = day_info
            if not args.compare:
              # normal dump mode
              result = dump_key_value_online(day_info)
              print(f"{area}\t{ReportUtil.ljust_jp(day,10)}{result}")

  if args.compare:
    for day, area_info in perDayFilteredResult.items():
      print(day)
      for area, day_info in area_info.items():
        result = dump_key_value_online(day_info)
        print(f" {area}\t{result}")

  if args.open:
    ExecUtil.open(Weather.URL)




