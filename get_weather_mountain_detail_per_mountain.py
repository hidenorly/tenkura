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


import os
import platform
import json
from html import unescape
from selenium import webdriver
import urllib.parse
import argparse
import time
import datetime
from bs4 import BeautifulSoup
from tenkura_get_weather import TenkuraFilterUtil
from tenkura_get_weather import MountainFilterUtil
try:
    from mountain_weather_dic import mountain_weather_dic
except:
    pass

from WeatherUtil import JsonCache, WebUtil, ExecUtil, ReportUtil


class MountainWeather:
    def __init__(self):
        self.driver = None
        self.cache = JsonCache(os.path.join(JsonCache.DEFAULT_CACHE_BASE_DIR, "weather_detail_per_mountain"), 1)


    def get_mountain_detail(self, url = "https://weathernews.jp/mountain/centralalps/40918/?target=trailhead"):
        _result = self.cache.restoreFromCache(url)
        if _result:
          return _result

        results = {}
        if not self.driver:
            self.driver = WebUtil.get_web_driver()
        driver = self.driver
        driver.get(url)
        base_url = driver.current_url
        time.sleep(3)

        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')

        astro_tag = soup.find('astro-island', {'component-export': 'default', 'component-url': lambda x: x and 'MyMountainButton' in x})

        mountain_name = url
        if astro_tag:
            props_json = unescape(astro_tag.get('props', ''))
            try:
                props = json.loads(props_json)
                mountain_data = props.get('mountainData')[1][0][1]
                mountain_name = mountain_data.get('mountain_name')[1]
                altitude = mountain_data.get('altitude')[1]
            except Exception as e:
                pass

        results[mountain_name] = {}

        # --- three days part
        threse_days = results[mountain_name]["threse_days"] = []

        blocks = soup.select("div.today__block")
        for block in blocks:
            date_text = block.select_one(".today__block-text").get_text(strip=True)
            day_number = date_text.split()[1]
            day_of_week = date_text.split()[2].strip("()")

            weather_text = block.select_one(".weather-text").get_text(strip=True)
            high_temp = block.select_one(".weather-temp .high").get_text(strip=True).replace("℃", "")
            low_temp = block.select_one(".weather-temp .low").get_text(strip=True).replace("℃", "")
            wind_dir = block.select_one(".weather-wind-dir").get_text(strip=True)
            wind_spd = block.select_one(".weather-wind-spd").get_text(strip=True).replace("m/s", "").strip()

            threse_days.append({
                "date": day_number,
                "wday": day_of_week,
                "weather": weather_text,
                "max_temp": high_temp,
                "min_temp": low_temp,
                "wind_direction": wind_dir,
                "wind": wind_spd,
            })

        # --- three days part
        per_hours = results[mountain_name]["per_hours"] = []

        blocks = soup.select('div.block[data-num]')

        for block in blocks:
            date_text = block.select_one('.date span').get_text(strip=True)
            rows = block.select('.row')
            for row in rows:
                _time = row.select_one('.time').get_text(strip=True).replace('時', '')
                weather_img = row.select_one('.weather img')
                weather_icon_url = weather_img['src'] if weather_img else ''
                temperature = row.select('p.value')[0].get_text(strip=True).replace('℃', '')
                precipitation = row.select('p.value')[1].get_text(strip=True).replace('mm', '')
                wind_div = row.select_one('.wind div')
                wind_speed = wind_div.select_one('p').get_text(strip=True).replace('m', '') if wind_div else ''
                wind_direction = wind_div['data-dir'] if wind_div and wind_div.has_attr('data-dir') else ''

                per_hours.append({
                    'date': date_text,
                    'hour': _time,
                    'weather_icon': weather_icon_url,
                    'temperature_c': temperature,
                    'precipitation_mm': precipitation,
                    'wind_speed_mps': wind_speed,
                    'wind_direction_deg': wind_direction,
                })

        #if results[url]:
        #    self.cache.storeToCache(url, results)
        return results

    def close(self):
        self.wait = None
        if self.driver:
            self.driver.quit()
        self.driver = None



if __name__=="__main__":
    parser = MountainWeather()
    result = parser.get_mountain_detail()
    for mountain_name, weathers in result.items():
        print(mountain_name)
        for key, _weathers in weathers.items():
            print(f"\t{key}")
            for weather in _weathers:
                for key, value in weather.items():
                    print(f"\t\t{ReportUtil.ljust_jp(key,10)}\t{ReportUtil.ljust_jp(value,10)}")
    parser.close()


