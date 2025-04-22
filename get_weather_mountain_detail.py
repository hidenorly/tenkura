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


import platform
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


class MountainWeather:
    weather_string = {
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
    }

    def __init__(self):
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        tempDriver = webdriver.Chrome(options=options)
        userAgent = tempDriver.execute_script("return navigator.userAgent")
        userAgent = userAgent.replace("headless", "")
        userAgent = userAgent.replace("Headless", "")

        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument(f"user-agent={userAgent}")
        self.driver = driver = webdriver.Chrome(options=options)
        driver.set_window_size(1920, 1080)


    def get_all_mountain(self, url = "https://weathernews.jp/mountain/hokkaido/?target=trailhead"):
        results = {}
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
                    pos1 = icon_url.rfind("/")
                    pos2 = icon_url.rfind(".")
                    weather_id = None
                    if pos1!=-1 and pos2!=-1:
                        weather_id = icon_url[pos1+1:pos2]
                        if weather_id in self.weather_string:
                            icon_url = self.weather_string[weather_id]
                    result["weather"].append({
                        "day" : date_list[i]['day'],
                        "wday" : date_list[i]['wday'],
                        "temperature_max" : high,
                        "temperature_min" : low,
                        "weather" : icon_url
                    })
                results[name] = result
                    #print(f"    {date_list[i]['day']}({date_list[i]['wday']}): {high}度/{low}度, 天気: {icon_url}")
        return results

    def close(self):
        self.wait = None
        self.driver.quit()
        self.driver = None

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
    for url, infos in mountain_weather_dic.items():
        if mountain_name in infos.keys():
            return url, infos[mountain_name]
        else:
            for candidate_mountain_name in infos.keys():
                if candidate_mountain_name.find(mountain_name)!=-1:
                    return url, infos[candidate_mountain_name]
    return None, None

def get_listurl_url_by_name(mountain_names):
    urls = set()
    results = {}
    for mountain_name in mountain_names:
        url, info = get_weather_url_info_by_name(mountain_name)
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


if __name__=="__main__":
    parser = argparse.ArgumentParser(description='Parse command line options.')
    parser.add_argument('args', nargs='*', help='mountain name such as 富士山')
    parser.add_argument('-d', '--date', action='store', default='', help='specify date e.g. 2/14,2/16-2/17')
    parser.add_argument('-dw', '--dateweekend', action='store_true', help='specify if weekend (Saturday and Sunday)')
    parser.add_argument('-w', '--excludeWeatherConditions', action='store', default='', help='specify excluding weather conditions e.g. rain,thunder default is none then all weathers are ok)')
    parser.add_argument('-nn', '--noDetails', action='store_true', default=False, help='specify if you want to output mountain name only')
    parser.add_argument('-e', '--exclude', action='append', default=[], help='specify excluding mountain list file e.g. climbedMountains.lst')
    parser.add_argument('-i', '--include', action='append', default=[], help='specify including mountain list file e.g. climbedMountains.lst')
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
    try:
        urls, infoDic = get_listurl_url_by_name(mountains)
    except:
        pass
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
            if is_matched_mountain(name, mountains):
                for aWeather in result["weather"]:
                    if isMatchedDate(aWeather["day"], specifiedDates) and is_matched_weather(aWeather["weather"], acceptableWeatherConditions):
                        if not name in filtered_results:
                            filtered_results[name] = []
                        filtered_results[name].append(aWeather)
                        filtered_mountains.add(name)

    if args.noDetails:
        # name only
        print(" ".join(list(filtered_mountains)))
    else:
        # normal dump
        for name, weathers in filtered_results.items():
            print( f'{name} ({unified_results[name]["url"]})' )
            for aWeather in weathers:
                print(f"{aWeather["day"]}({aWeather["wday"]}) {aWeather["temperature_max"]}度/{aWeather["temperature_min"]}度, 天気: {aWeather["weather"]}")

    weather.close()



