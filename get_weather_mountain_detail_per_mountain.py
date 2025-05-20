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
import re
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

from WeatherUtil import JsonCache, WebUtil, ExecUtil, ReportUtil, WeatherConstants, WeatherUtils


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
                "high_temp": high_temp,
                "low_temp": low_temp,
                "wind": wind_spd,
                "wind_direction": wind_dir,
            })

        # --- three days part
        per_hours = results[mountain_name]["per_hours"] = []

        blocks = soup.select('div.block[data-num]')

        for block in blocks:
            date_text = block.select_one('.date span').get_text(strip=True)
            pos1 = date_text.find("(")
            pos2 = date_text.find(")")
            day = date_text[0:pos1]
            match = re.search(r'\d+', day)
            if match:
                day = int(match.group())
            wday = date_text[pos1+1:pos2]
            rows = block.select('.row')
            for row in rows:
                _time = row.select_one('.time').get_text(strip=True).replace('時', '')
                weather_img = row.select_one('.weather img')
                weather_icon_url = weather_img['src'] if weather_img else ''
                weather_icon_url = WeatherConstants.get_weather_desc(weather_icon_url)
                temperature = row.select('p.value')[0].get_text(strip=True).replace('℃', '')
                precipitation = row.select('p.value')[1].get_text(strip=True).replace('mm', '')
                wind_div = row.select_one('.wind div')
                wind_speed = wind_div.select_one('p').get_text(strip=True).replace('m', '') if wind_div else ''
                wind_direction = wind_div['data-dir'] if wind_div and wind_div.has_attr('data-dir') else ''

                per_hours.append({
                    'date': day,
                    'wday': wday,
                    'hour': _time,
                    'weather': weather_icon_url,
                    'temperature': temperature,
                    'precipitation_mm': precipitation,
                    'wind': wind_speed,
                    'wind_direction': wind_direction,
                })

        # --- weekly part
        weekly_forecast = results[mountain_name]["per_days"] = []
        blocks = soup.select('.week-item')

        for block in blocks:
            day = block.select_one('.week-date-wday')
            date = block.select_one('.week-date-date')
            icon = block.select_one('.week-wx-image img')
            high = block.select_one('.week-high')
            low = block.select_one('.week-low')

            forecast = {
                'date': date.text if date else None,
                'wday': day.text if day else None,
                'weather': WeatherConstants.get_weather_desc(icon['src']) if icon else None,
                'high_temp': high.text.replace('℃', '').strip() if high else None,
                'low_temp': low.text.replace('℃', '').strip() if low else None
            }

            weekly_forecast.append(forecast)

        if results:
            self.cache.storeToCache(url, results)

        return results

    def close(self):
        self.wait = None
        if self.driver:
            self.driver.quit()
        self.driver = None


def filter_specified_dates(results, targetDates):
    filtered_result = {}
    for mountain_name, infos in results.items():
        _infos = {}
        for category, data in infos.items():
            for aData in data:
                if WeatherUtils.isMatchedDate(aData["date"], targetDates):
                    if not category in _infos:
                        _infos[category] = []
                    _infos[category].append(aData)
        filtered_result[mountain_name] = _infos
    return filtered_result


def filter_weather_conditions(results, acceptableWeatherConditions):
    filtered_result = {}

    for mountain_name, infos in results.items():
        # --- calculate weather condition accepted dates
        available_dates = set()
        unavailable_dates = set()
        for category, data in infos.items():
            for aData in data:
                available_dates.add(int(aData["date"]))
                if not WeatherUtils.is_matched_weather(aData["weather"], acceptableWeatherConditions):
                    unavailable_dates.add(int(aData["date"]))

        available_dates = available_dates - unavailable_dates

        formulated_available_dates = set()
        for _day in list(available_dates):
            # make it standard date e.g. 10 -> 5/10
            for __day in TenkuraFilterUtil.getListOfDates( str(_day) ):
                formulated_available_dates.add( __day )

        # --- filter with the calculate weather condition accepted dates
        if formulated_available_dates:
            _filtered_result = filter_specified_dates( { mountain_name : infos }, list(formulated_available_dates) )
            filtered_result.update( _filtered_result )

    return filtered_result


def filter_time_conditions(results, startTime, endTime):
    if startTime==0 and endTime==24:
        return results

    filtered_result = {}
    for mountain_name, infos in results.items():
        filtered_result[mountain_name] = {}

        # extract per-hour found dates
        time_found_dates = set()
        if "per_hours" in infos:
            filtered_per_hours = []
            for data in infos["per_hours"]:
                time_found_dates.add(int(data["date"]))
                if "hour" in data:
                    hour = int(data["hour"])
                    if hour>=startTime and hour<=endTime:
                        filtered_per_hours.append(data)
                else:
                    filtered_per_hours.append(data)
            filtered_result[mountain_name]["per_hours"] = filtered_per_hours

        # omit data for per-hour found dates' data
        omit_keys = set(infos.keys()) - set("per_hours")
        for key in list(omit_keys):
            _tmp = []
            for data in infos[key]:
                if not int(data["date"]) in time_found_dates:
                    _tmp.append(data)
            if _tmp:
                filtered_result[mountain_name][key] = _tmp

    return filtered_result


def get_standarized_weather(weather):
    weather = weather.strip()
    pos = weather.find("(")
    if pos!=-1:
        weather = weather[0:pos]
    weather = weather.strip()
    return weather

def get_fallback_weather(weathers):
    if not weathers:
        return None

    result = "fine"
    if "cloud" in weathers:
        result = "cloud"
    if "thunder" in weathers:
        result = "thunder"
    if "snow" in weathers:
        result = "snow"
    if "rain" in weathers:
        result = "rain"
    return result


def get_fallbacked_weathers(weathers):
    weather1 = set()
    weather2 = set()
    for weather in weathers:
        pos = weather.find("_")
        if pos!=-1:
            weather1.add( get_standarized_weather(weather[0:pos]) )
            weather2.add( get_standarized_weather(weather[pos+1:]) )
        else:
            weather1.add( get_standarized_weather(weather) )
    weather1 = get_fallback_weather(weather1)
    weather2 = get_fallback_weather(weather2)
    if not weather2 or weather1==weather2:
        return weather1
    return f"{weather1}_{weather2}"


def reconstruct_perday_from_filtered_perhour(results):
    reconstruct_result = {}
    for mountain_name, infos in results.items():
        reconstruct_result[mountain_name] = infos

        # extract per-hour found dates
        time_found_dates = set()
        per_day = []
        for i in range(32):
            per_day.append([])
        if "per_hours" in infos:
            for data in infos["per_hours"]:
                time_found_dates.add(int(data["date"]))
                if "date" in data:
                    date = int(data["date"])
                    per_day[date].append(data["weather"])
        for i in range(32):
            if per_day[i]:
                weather = per_day[i] = get_fallbacked_weathers(per_day[i])
                if weather:
                    the_day_info = {
                        "date": i,
                        "wday": "",
                        "weather": weather,
                        "high_temp": "",
                        "low_temp": ""
                    }
                    if not "per_days" in reconstruct_result[mountain_name]:
                        reconstruct_result[mountain_name]["per_days"] = []
                    reconstruct_result[mountain_name]["per_days"].append(the_day_info)

    return reconstruct_result



if __name__=="__main__":
    parser = argparse.ArgumentParser(description='Parse command line options.')
    parser.add_argument('args', nargs='*', help='mountain name such as 富士山')
    parser.add_argument('-t', '--time', action='store', default='0-24', help='specify time range e.g. 6-15')
    parser.add_argument('-d', '--date', action='store', default='', help='specify date e.g. 2/14,2/16-2/17')
    parser.add_argument('-dw', '--dateweekend', action='store_true', help='specify if weekend (Saturday and Sunday)')
    parser.add_argument('-w', '--excludeWeatherConditions', action='store', default='', help='specify excluding weather conditions e.g. rain,thunder default is none then all weathers are ok)')
    parser.add_argument('-nn', '--noDetails', action='store_true', default=False, help='specify if you want to output mountain name only')
    parser.add_argument('-e', '--exclude', action='append', default=[], help='specify excluding mountain list file e.g. climbedMountains.lst')
    parser.add_argument('-i', '--include', action='append', default=[], help='specify including mountain list file e.g. climbedMountains.lst')
    parser.add_argument('-c', '--compare', action='store_true', help='compare mountains per day')
    args = parser.parse_args()


    startTime, endTime = TenkuraFilterUtil.getTimeRange( args.time )

    acceptableWeatherConditions = TenkuraFilterUtil.getAcceptableWeatherConditions( args.excludeWeatherConditions.split(",") )

    specifiedDates = TenkuraFilterUtil.getListOfDates( args.date )
    if args.dateweekend:
        weekEndDates = TenkuraFilterUtil.getWeekEndYYMMDD( datetime.datetime.now(), False )
        specifiedDates.extend(weekEndDates)
        specifiedDates = list(set(filter(None,specifiedDates)))
        specifiedDates.sort(key=TenkuraFilterUtil.dateSortUtil)

    parser = MountainWeather()

    mountains = MountainFilterUtil.mountainsIncludeExcludeFromFile( set(args.args), args.exclude, args.include )
    urls, infoDic = WeatherUtils.get_listurl_url_by_name(mountains)

    results = {}
    for mountainName, url in infoDic.items():
        _result = parser.get_mountain_detail(url)
        _result = filter_specified_dates( _result, specifiedDates )
        _result = filter_time_conditions( _result, startTime, endTime )
        _result = filter_weather_conditions( _result, acceptableWeatherConditions )
        if _result and mountainName in _result and _result[mountainName]:
            results.update(_result)

    if args.noDetails:
        # dump just names
        print(" ".join(sorted(results.keys())))
    else:
        if args.compare:
            # --- compare mode
            results = reconstruct_perday_from_filtered_perhour(results)
            # extract available days
            available_days = set()
            for mountain_name, weathers in results.items():
                if "per_days" in weathers:
                    for data in weathers["per_days"]:
                        available_days.add( int(data["date"]) )
            #available_days = sorted( available_days )
            mountain_names = sorted( results.keys() )

            # extract data per available days per mountain
            weathers = {}
            for mountain_name in mountain_names:
                weather_infos = results[mountain_name]
                if "per_days" in weather_infos:
                    info = []
                    for target_day in available_days:
                        is_found = False
                        for day_info in weather_infos["per_days"]:
                            if int(day_info["date"]) == target_day:
                                info.append( day_info["weather"] )
                                is_found = True
                                break
                        if not is_found:
                            info.append( "" )
                    weathers[mountain_name] = info

            # show the extracted data per available days per mountain
            ## print 1st line (name day1 day2...)
            the_info = ""
            for day in available_days:
                the_info += (ReportUtil.ljust_jp(str(day), 12) + " ")
            print(f'{ReportUtil.ljust_jp("name",15)} {the_info}')
            ## print actual info as name day1 day2...
            for mountain_name, day_infos in weathers.items():
                the_info = ""
                for day_info in day_infos:
                    the_info += (ReportUtil.ljust_jp(day_info, 12) + " ")
                print(f"{ReportUtil.ljust_jp(mountain_name,15)} {the_info}")

        else:
            # dump everything
            for mountain_name, weathers in results.items():
                print(mountain_name)
                for key, _weathers in weathers.items():
                    print(f"\t{key}")
                    for weather in _weathers:
                        for key, value in weather.items():
                            print(f"\t\t{ReportUtil.ljust_jp(key,10)}\t{ReportUtil.ljust_jp(str(value),10)}")
                        print("")

    parser.close()


