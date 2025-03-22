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
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from PIL import Image
from io import BytesIO

import time

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
driver.set_window_size(1000, 1080)

driver.get("https://weathernews.jp/mountain/")
wait = WebDriverWait(driver, 2)


def zoom_in_map(times=3):
	zoom_in_button = driver.find_element(By.CSS_SELECTOR, "a.leaflet-control-zoom-in")
	if not zoom_in_button:
		zoom_in_button = driver.find_element(By.XPATH, "//a[@class='leaflet-control-zoom-in']")
	if not zoom_in_button:
		zoom_in_button = driver.find_element(By.XPATH, "//a[span[text()='+']]")
	if zoom_in_button:
		for _ in range(times):
			zoom_in_button.click()
			time.sleep(0.1)

def move_map(x_offset, y_offset):
    map_element = wait.until(EC.presence_of_element_located((By.ID, "map")))

    if map_element:
        actions = ActionChains(driver)
        actions.click_and_hold(map_element).move_by_offset(x_offset, y_offset).release().perform()
        time.sleep(0.1)
    else:
        print("Unable to find the map")


def scroll_until_visible(wday):
	body = driver.find_element(By.TAG_NAME, "body")
	while True:
		button = wait.until(EC.element_to_be_clickable((By.XPATH, f"//button[p/span[text()='{wday}']]")))
		try:
			# try to click (assume to receive exception)
			button.click()
			# not received case menas found it!
			time.sleep(0.1)
			return
		except:
			pass
		body.send_keys(Keys.ARROW_DOWN)
		time.sleep(0.1)


def cropped_capture(filename, sx, sy, ex, ey):
	png = driver.get_screenshot_as_png()

	image = Image.open(BytesIO(png))
	image = image.crop((sx, sy, ex, ey))
	image.save(filename)


def select_date_and_capture(wday, filename):
	button = wait.until(EC.element_to_be_clickable((By.XPATH, f"//button[p/span[text()='{wday}']]")))
	if button:
		button.click()
		time.sleep(1)
		map_element = None
		#map_element = wait.until(EC.presence_of_element_located((By.ID, "map")))
		if map_element:
			map_element.screenshot(filename)
		else:
			#driver.save_screenshot(filename)
			cropped_capture(filename, 26,253+198+78, 1134+10,1200+198+78*3)


# wait
wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "a.leaflet-control-zoom-in")))

# zoom in
zoom_in_map(7)
move_map(-100,-100)
move_map(-100,-80)
move_map(-100,0)
move_map(-50,0)

# scroll down to find calendar
scroll_until_visible("土")

# capture specified date's weather
select_date_and_capture("土", "saturday.png")
select_date_and_capture("日", "sunday.png")

# finalize
driver.quit()
