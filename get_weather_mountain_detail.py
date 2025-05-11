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
from selenium import webdriver
import urllib.parse
import argparse
import time
import datetime
from bs4 import BeautifulSoup
from tenkura_get_weather import TenkuraFilterUtil
from tenkura_get_weather import MountainFilterUtil

from WeatherUtil import JsonCache, WebUtil, ExecUtil, ReportUtil, WeatherConstants, WeatherUtils


class MountainWeather:
    def __init__(self):
        self.driver = None
        self.cache = JsonCache(os.path.join(JsonCache.DEFAULT_CACHE_BASE_DIR, "weather_detail"), 1)

    def get_all_mountain(self, url = "https://weathernews.jp/mountain/hokkaido/?target=trailhead"):
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

        # retreive all of calendar
        calendars = soup.select('div.calendar.is-fixed.is-web')

        for calendar in calendars:
            result = {}
            # parse area
            area_name = calendar.select_one('.head-text').get_text(strip=True)

            # parse date and week header
            date_blocks = calendar.select('.head .date')
            date_list = []
            for date in date_blocks:
                if date.get('style') == 'display: none;':
                    continue
                day = date.select_one('.date-text').get_text(strip=True)
                wday = date.select_one('.date-wday').get_text(strip=True)
                date_list.append({'day': day, 'wday': wday})

            # parse each mountain
            rows = calendar.select('.body a.row')
            for row in rows:
                name = row.select_one('.mountain .name').get_text(strip=True)
                relative_url = row.get('href')
                absolute_url = urllib.parse.urljoin(base_url, relative_url)
                result = {
                    "name": name,
                    "url" : absolute_url,
                    "weather": []
                }
                temps = row.select('.week')
                for i, week in enumerate(temps[:len(date_list)]):  # fit to number of date_list
                    wx_img = week.select_one('.wx img')
                    high = week.select_one('.high').get_text(strip=True)
                    low = week.select_one('.low').get_text(strip=True)
                    icon_url = wx_img['src'] if wx_img else None
                    icon_url = WeatherConstants.get_weather_desc(icon_url)

                    result["weather"].append({
                        "day" : date_list[i]['day'],
                        "wday" : date_list[i]['wday'],
                        "temperature_max" : high,
                        "temperature_min" : low,
                        "weather" : icon_url
                    })
                results[name] = result
                    #print(f"    {date_list[i]['day']}({date_list[i]['wday']}): {high}度/{low}度, 天気: {icon_url}")

        if results:
            self.cache.storeToCache(url, results)
        return results

    def close(self):
        self.wait = None
        if self.driver:
            self.driver.quit()
        self.driver = None



if __name__=="__main__":
    parser = argparse.ArgumentParser(description='Parse command line options.')
    parser.add_argument('args', nargs='*', help='mountain name such as 富士山')
    parser.add_argument('-d', '--date', action='store', default='', help='specify date e.g. 2/14,2/16-2/17')
    parser.add_argument('-dw', '--dateweekend', action='store_true', help='specify if weekend (Saturday and Sunday)')
    parser.add_argument('-w', '--excludeWeatherConditions', action='store', default='', help='specify excluding weather conditions e.g. rain,thunder default is none then all weathers are ok)')
    parser.add_argument('-nn', '--noDetails', action='store_true', default=False, help='specify if you want to output mountain name only')
    parser.add_argument('-e', '--exclude', action='append', default=[], help='specify excluding mountain list file e.g. climbedMountains.lst')
    parser.add_argument('-i', '--include', action='append', default=[], help='specify including mountain list file e.g. climbedMountains.lst')
    parser.add_argument('-c', '--compare', action='store_true', help='compare mountains per day')
    parser.add_argument('-s', '--stat', action='store_true', help='dump count of mountains per day. Should use with -w')
    parser.add_argument('-o', '--openUrl', action='store_true', default=False, help='specify if you want to open the url')
    args = parser.parse_args()

    mountains = MountainFilterUtil.mountainsIncludeExcludeFromFile( set(args.args), args.exclude, args.include )
    acceptableWeatherConditions = TenkuraFilterUtil.getAcceptableWeatherConditions( args.excludeWeatherConditions.split(",") )

    specifiedDates = TenkuraFilterUtil.getListOfDates( args.date )
    if args.dateweekend:
        weekEndDates = TenkuraFilterUtil.getWeekEndYYMMDD( datetime.datetime.now(), False )
        specifiedDates.extend(weekEndDates)
        specifiedDates = list(set(filter(None,specifiedDates)))
        specifiedDates.sort(key=TenkuraFilterUtil.dateSortUtil)

    urls = set()
    urls.add("https://weathernews.jp/mountain/kanto/?target=trailhead")
    infoDic = {}
    open_urls  = set()
    urls, infoDic = WeatherUtils.get_listurl_url_by_name(mountains)
    #print(f"urls={str(urls)}")
    #print(f"infoDic={str(infoDic)}")
    #print(str(specifiedDates))
    filtered_mountains = set()


    weather = MountainWeather()
    filtered_results = {}
    unified_results = {}
    for list_url in urls:
        results = weather.get_all_mountain(list_url)
        unified_results.update(results)
        for name, result in results.items():
            if WeatherUtils.is_matched_mountain(name, mountains):
                for aWeather in result["weather"]:
                    if WeatherUtils.isMatchedDate(aWeather["day"], specifiedDates) and WeatherUtils.is_matched_weather(aWeather["weather"], acceptableWeatherConditions):
                        if not name in filtered_results:
                            filtered_results[name] = []
                        filtered_results[name].append(aWeather)
                        filtered_mountains.add(name)

    if args.noDetails:
        # name only
        print(" ".join(list(filtered_mountains)))
    else:
        # normal dump
        if args.compare or args.stat:
            # per-day
            for aDay in specifiedDates:
                isDayOutput = False
                pos = aDay.rfind("/")
                iDay = 0
                count = 0
                if pos!=-1:
                    iDay = int(aDay[pos+1:])
                for name, weathers in filtered_results.items():
                    for aWeather in weathers:
                        if int(aWeather["day"])==iDay:
                            count += 1
                            if not args.stat:
                                if not isDayOutput:
                                    print(f'\n{aWeather["day"]}({aWeather["wday"]}):')
                                    isDayOutput = True
                                print(f'\t{ReportUtil.ljust_jp(name, 15)}\t{ReportUtil.ljust_jp(aWeather["weather"], 14)}\t{aWeather["temperature_max"]}度/{aWeather["temperature_min"]}度')
                                open_urls.add(unified_results[name]["url"])
                if args.stat:
                    print(f'{aDay} : {count}')
        else:
            # per-mountain
            for name, weathers in filtered_results.items():
                print( f'{ReportUtil.ljust_jp(name, 14)} ({unified_results[name]["url"]})' )
                for aWeather in weathers:
                    print(f'\t{aWeather["day"]}({aWeather["wday"]}) {ReportUtil.ljust_jp(aWeather["weather"], 14)} {aWeather["temperature_max"]}度/{aWeather["temperature_min"]}度')
                    open_urls.add(unified_results[name]["url"])

    weather.close()

    if args.openUrl:
        n = 0
        for an_url in open_urls:
            n = n + 1
            if n>2:
                time.sleep(0.5)
            ExecUtil.open(an_url)


