#!/usr/bin/env python3
# coding: utf-8
#   Copyright 2024 hidenorly
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


import datetime
import argparse
import sys
import subprocess
import urllib.parse
from urllib.parse import urljoin
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re
from tenkura_get_weather import TenkuraFilterUtil
from tenkura_get_weather import ReportUtil

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
    options.add_argument('--headless')
    options.add_argument(f"user-agent={userAgent}")
    driver = webdriver.Chrome(options=options)
    driver.set_window_size(width, height)

    return driver

class Weather:
  URL = "https://www.jma.go.jp/bosai/forecast/"

  def __init__(self, driver = None):
    if not driver:
      self._driver = WebUtil.get_web_driver()
    else:
      self._driver = driver

  def get_weather(self):
    forecast_data = {}

    driver = self._driver
    if driver:
      driver.get(self.URL)

      WebDriverWait(driver, 10).until(
          EC.presence_of_element_located((By.ID, 'week-table-container'))
      )
      WebDriverWait(driver, 10).until(
        lambda d: d.find_element(By.ID, 'week-table-container').get_attribute('innerHTML').strip() != ""
      )

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

    return forecast_data

def dump_key_value_online(day_info):
    result = ""
    for key,value in day_info.items():
      result=f"{result}   {ReportUtil.ljust_jp(value, max_length[key])}"
    return result


if __name__=="__main__":
  parser = argparse.ArgumentParser(description='Specify expected prefectures')
  parser.add_argument('args', nargs='*', help='')
  parser.add_argument('-d', '--date', action='store', default='', help='specify date e.g. 2/14,2/16-2/17')
  parser.add_argument('-dw', '--dateweekend', action='store_true', help='specify if weekend (Saturday and Sunday)')
  parser.add_argument('-c', '--compare', action='store_true', help='compare per day')

  args = parser.parse_args()

  specifiedDates = TenkuraFilterUtil.getListOfDates( args.date )
  if args.dateweekend:
    weekEndDates = TenkuraFilterUtil.getWeekEndYYMMDD( datetime.datetime.now(), False )
    specifiedDates.extend(weekEndDates)
    specifiedDates = list(set(filter(None,specifiedDates)))
    specifiedDates.sort(key=TenkuraFilterUtil.dateSortUtil)

  driver = WebUtil.get_web_driver()
  weather = Weather()
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
    if not args.args or area in args.args:
      for day, day_info in area_info.items():
        _day = TenkuraFilterUtil.ensureYearMonth(day.split("日")[0])
        if not specifiedDates or (TenkuraFilterUtil.isMatchedDate(_day, specifiedDates)):
          if not _day in perDayFilteredResult:
            perDayFilteredResult[_day] = {}
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




