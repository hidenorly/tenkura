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


import argparse
import platform
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from PIL import Image
from io import BytesIO

import time

class WeatherNews:
	def __init__(self):
		options = webdriver.ChromeOptions()
		options.add_argument('--headless')
		tempDriver = webdriver.Chrome(options=options)
		userAgent = tempDriver.execute_script("return navigator.userAgent")
		userAgent = userAgent.replace("headless", "")
		userAgent = userAgent.replace("Headless", "")

		dpi_info = tempDriver.execute_script("""
		    return {
		        devicePixelRatio: window.devicePixelRatio,
		        screenWidth: screen.width,
		        screenHeight: screen.height,
		        screenAvailWidth: screen.availWidth,
		        screenAvailHeight: screen.availHeight
		    };
		""")
		self.density = dpi_info["devicePixelRatio"]
		os_name = platform.system()
		self.offset_x = 0
		self.offset_y = 0
		if os_name == "Darwin":
			self.offset_x = 0
			self.offset_y = 90

		options = webdriver.ChromeOptions()
		options.add_argument('--headless')
		options.add_argument(f"user-agent={userAgent}")
		self.driver = driver = webdriver.Chrome(options=options)
		driver.set_window_size(1000, 1080)

	def open(self):
		driver = self.driver
		driver.get("https://weathernews.jp/mountain/")
		self.wait = wait = WebDriverWait(driver, 2)
		try:
			wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "a.leaflet-control-zoom-in")))
		except:
			pass

		# zoom in
		self.zoom_in_map(7)
		self.move_map(-100,-100)
		self.move_map(-100,-80)
		self.move_map(-100,0)
		self.move_map(-50,0)

		# scroll down to find calendar
		self.scroll_until_visible("土")


	def zoom_in_map(self, times=3):
		driver = self.driver
		zoom_in_button = driver.find_element(By.CSS_SELECTOR, "a.leaflet-control-zoom-in")
		if not zoom_in_button:
			zoom_in_button = driver.find_element(By.XPATH, "//a[@class='leaflet-control-zoom-in']")
		if not zoom_in_button:
			zoom_in_button = driver.find_element(By.XPATH, "//a[span[text()='+']]")
		if zoom_in_button:
			for _ in range(times):
				zoom_in_button.click()
				time.sleep(0.1)

	def move_map(self, x_offset, y_offset):
		driver = self.driver
		wait = self.wait
		map_element = None
		try:
			map_element = wait.until(EC.presence_of_element_located((By.ID, "map")))
		except:
			pass

		if map_element:
			actions = ActionChains(driver)
			actions.click_and_hold(map_element).move_by_offset(x_offset, y_offset).release().perform()
			time.sleep(0.1)
		else:
			print("Unable to find the map")


	def scroll_until_visible(self, wday):
		driver = self.driver
		wait = self.wait
		body = driver.find_element(By.TAG_NAME, "body")
		button = None
		while True:
			try:
				button = wait.until(EC.element_to_be_clickable((By.XPATH, f"//button[p/span[text()='{wday}']]")))
				# try to click (assume to receive exception)
				button.click()
				# not received case menas found it!
				time.sleep(0.1)
				return
			except:
				pass
			body.send_keys(Keys.ARROW_DOWN)
			time.sleep(0.1)


	def cropped_capture(self, filename, sx, sy, ex, ey):
		driver = self.driver
		png = driver.get_screenshot_as_png()

		image = Image.open(BytesIO(png))
		image = image.crop((sx, sy, ex, ey))
		image.save(filename)

	WEEK_FILENAME = {
		"月" : "monday.png",
		"火" : "tuesday.png",
		"水" : "wednesday.png",
		"木" : "thursday.png",
		"金" : "friday.png",
		"土" : "saturday.png",
		"日" : "sunday.png"
	}

	def select_date_and_capture(self, wday, filename = None):
		driver = self.driver
		wait = self.wait
		button = None
		try:
			#button = wait.until(EC.element_to_be_clickable((By.XPATH, f"//button[p/span[text()='{wday}']]")))
			xpath = (
				f"//button[p[contains(text(), '{wday}') or span[contains(text(), '{wday}')]]]"
			)
			button = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
		except:
			pass
		if button:
			date_text = button.find_element(By.CSS_SELECTOR, ".week-item-text").get_attribute("innerText").strip()
			wday_text = button.find_element(By.CSS_SELECTOR, ".week-item-wday").text.strip()
			day_only = date_text.replace(wday_text, "").strip()
			#print(f"Date: {day_only}, Week: {wday_text}")	
			button.click()
			time.sleep(1)
			map_element = None
			#map_element = wait.until(EC.presence_of_element_located((By.ID, "map")))
			if not filename:
				if wday_text in self.WEEK_FILENAME:
					filename = self.WEEK_FILENAME[wday_text]
				else:
					filename = "weather_map.png"
			if map_element:
				map_element.screenshot(filename)
			else:
				#driver.save_screenshot(filename)
				self.cropped_capture(filename, 13*self.density, 220*self.density+self.offset_y, 568*self.density, 779*self.density+self.offset_y)
				#self.cropped_capture(filename, 26,				253+198+78, 	  1134+10,			1200+198+78*3)

	def get_weathers(self, requests):
		for wday, filename in requests.items():
			self.select_date_and_capture(wday, filename)

	def get_weathers_map(self, wdays):
		for wday in wdays:
			self.select_date_and_capture(wday)

	def close(self):
		self.wait = None
		self.driver.quit()
		self.driver = None


if __name__=="__main__":
	parser = argparse.ArgumentParser(description='Parse command line options.')
	parser.add_argument('args', nargs='*', help='mountain name such as 富士山')
	parser.add_argument('-d', '--date', action='store', default='', help='specify date e.g. 2/14,2/16-2/17')
	parser.add_argument('-dw', '--dateweekend', action='store_true', help='specify if weekend (Saturday and Sunday)')
	args = parser.parse_args()

	target_dates = set()
	if args.date:
	    target_dates.update(str(args.date).split(","))
	if args.dateweekend:
	    target_dates.update(["土", "日"])

	news = WeatherNews()
	news.open()
	#news.get_weathers( {"土":"saturday.png", "日":"sunday.png"} )
	news.get_weathers_map(target_dates)
	news.close()
