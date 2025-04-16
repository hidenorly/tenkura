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
    "302": "rain_rain",
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

options = webdriver.ChromeOptions()
options.add_argument('--headless')
driver = webdriver.Chrome(options=options)
driver.set_window_size(1920, 1080)


driver.get("https://weathernews.jp/mountain/hokkaido/?target=trailhead")
base_url = driver.current_url
time.sleep(3)  # ページが読み込まれるまで待機（必要に応じて調整）

# HTMLを取得
html = driver.page_source
soup = BeautifulSoup(html, 'html.parser')

# 複数ある calendar をすべて取得
calendars = soup.select('div.calendar.is-fixed.is-web')

for calendar in calendars:
    print('---')

    # エリア名（例: 利尻・礼文）
    area_name = calendar.select_one('.head-text').get_text(strip=True)
    print(f"エリア名: {area_name}")

    # 日付・曜日のヘッダ部分
    date_blocks = calendar.select('.head .date')
    date_list = []
    for date in date_blocks:
        if date.get('style') == 'display: none;':
            continue
        day = date.select_one('.date-text').get_text(strip=True)
        wday = date.select_one('.date-wday').get_text(strip=True)
        date_list.append({'day': day, 'wday': wday})
    #print("日付:", date_list)

    # 各山の天気予報データ
    rows = calendar.select('.body a.row')
    for row in rows:
        name = row.select_one('.mountain .name').get_text(strip=True)
        relative_url = row.get('href')
        absolute_url = urllib.parse.urljoin(base_url, relative_url)
        print(f"\n  山名: {name}（URL: {absolute_url}）")
        temps = row.select('.week')
        for i, week in enumerate(temps[:len(date_list)]):  # date_listの数に合わせる
            wx_img = week.select_one('.wx img')
            high = week.select_one('.high').get_text(strip=True)
            low = week.select_one('.low').get_text(strip=True)
            icon_url = wx_img['src'] if wx_img else None
            pos1 = icon_url.rfind("/")
            pos2 = icon_url.rfind(".")
            weather_id = None
            if pos1!=-1 and pos2!=-1:
                weather_id = icon_url[pos1+1:pos2]
                if weather_id in weather_string:
                    icon_url = weather_string[weather_id]
            print(f"    {date_list[i]['day']}({date_list[i]['wday']}): {high}度/{low}度, 天気: {icon_url}")

driver.quit()




