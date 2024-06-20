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

        for region in regions:
          _forecast_data = {}
          # area
          area_name_elements = region.find_elements(By.CLASS_NAME, 'forecast-area')
          area_name = None
          for area_name_element in area_name_elements:
            area_name = area_name_element.text.strip()
            if area_name and not area_name in _forecast_data:
              _forecast_data[area_name] = {}

          # dates
          _dates = [e.text for e in region.find_elements(By.CLASS_NAME, 'forecast-date')]
          dates = {}
          for _date in _dates:
            if _date and not _date in dates:
              dates[_date] = True
          dates = dates.keys()

          # weather
          weather_elements = region.find_elements(By.CLASS_NAME, 'forecast-icon')
          weathers = [e.get_attribute("title") for e in weather_elements]

          # Extract precipitation probability
          precip_prob_elements = region.find_elements(By.XPATH, f".//tr[th[contains(text(), '降水確率')]]")
          _precip_probs = [e.text for e in precip_prob_elements]
          precip_probs = []
          for prob in _precip_probs:
            if prob:
              precip_probs.append(prob)
          
          # Extract confidence data
          confidence_elements = region.find_elements(By.XPATH, f".//tr[th[contains(text(), '信頼度')]]")
          _confidences = [e.text for e in confidence_elements]
          confidences =[]
          for confidence in _confidences:
            if confidence:
              confidences.append(confidence)

          # Extract temperature
          temperature_elements = region.find_elements(By.XPATH, f".//tr[th[div[contains(text(), '最低')]]]")
          _temperatures = [e.text for e in temperature_elements]
          temperatures = []
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


if __name__=="__main__":
  parser = argparse.ArgumentParser(description='Specify expected prefectures')
  parser.add_argument('args', nargs='*', help='')

  args = parser.parse_args()

  driver = WebUtil.get_web_driver()
  weather = Weather()
  result = weather.get_weather()
  
  for area, area_info in result.items():
    for day, day_info in area_info.items():
      print(f"{area}:{day}:{str(day_info)}")




