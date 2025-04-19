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
import time
from bs4 import BeautifulSoup


from get_weather_mountain_detail import MountainWeather

mountain_weather_list=[
    "https://weathernews.jp/mountain/hokkaido/?target=trailhead",
    "https://weathernews.jp/mountain/tohoku/?target=trailhead",
    "https://weathernews.jp/mountain/kanto/?target=trailhead",
    "https://weathernews.jp/mountain/kanto/?area=oze_nasu_nikko&target=trailhead",
    "https://weathernews.jp/mountain/fuji/?target=trailhead",
    "https://weathernews.jp/mountain/koshinetsu/?target=trailhead",
    "https://weathernews.jp/mountain/yatsugatake/?target=trailhead",
    "https://weathernews.jp/mountain/northernalps/?target=trailhead",
    "https://weathernews.jp/mountain/centralalps/?target=trailhead",
    "https://weathernews.jp/mountain/southernalps/?target=trailhead",
    "https://weathernews.jp/mountain/tokai_hokuriku/?target=trailhead",
    "https://weathernews.jp/mountain/kinki/?target=trailhead",
    "https://weathernews.jp/mountain/chugoku/?target=trailhead",
    "https://weathernews.jp/mountain/shikoku/?target=trailhead",
    "https://weathernews.jp/mountain/kyushu/?target=trailhead"
]


if __name__=="__main__":
    print("mountain_weather_dic={")
    weather = MountainWeather()
    for url in mountain_weather_list:
        results = weather.get_all_mountain(url)
        print("\""+url+"\":{")
        for name, result in results.items():
            print( f'\t"{name}":"{results[name]["url"]}",')
        print("},")
    print("}")

    weather.close()



