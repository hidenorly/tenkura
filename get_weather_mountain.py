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
import time
import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    ElementNotInteractableException,
    TimeoutException,
    StaleElementReferenceException
)
from PIL import Image
from io import BytesIO
from tenkura_get_weather import TenkuraFilterUtil

import time
from selenium.webdriver.common.by import By

import threading
from selenium.webdriver.common.by import By

class AdWatcher:
	def __init__(self, driver, interval=0.5):
		self.driver = driver
		self.interval = interval
		self.running = False
		self.thread = None
		self.handlers = []

	def start(self):
		self.running = True
		self._schedule()

	def stop(self):
		self.running = False
		if self.thread:
			self.thread.cancel()

	def _schedule(self):
		if self.running:
			self.thread = threading.Timer(self.interval, self._check)
			self.thread.start()

	def _check(self):
		print("check...")
		if self.detect_ad():
			print("ad detected!")
			self.notify_handlers()
		self._schedule()

	def detect_ad(self):
		current_url = self.driver.current_url
		if "#google_vignette" in current_url:
			return True
		return False

		try:
			iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
			for iframe in iframes:
				self.driver.switch_to.frame(iframe)
				try:
					close_button = self.driver.find_element(By.CSS_SELECTOR, "div[aria-label='Close']")
					self.driver.switch_to.default_content()
					time.sleep(0.5)
					return True
				except:
					self.driver.switch_to.default_content()
					time.sleep(0.5)
					continue
		except:
			pass

		try:
			close_button = self.driver.find_element(By.CSS_SELECTOR, "div[aria-label='Close']")
			self.driver.switch_to.default_content()
			time.sleep(0.5)
			return True
		except:
			pass

		self.driver.switch_to.default_content()
		time.sleep(0.5)
		return False

	def notify_handlers(self):
		for handler in self.handlers:
			handler()

	def add_handler(self, handler_func):
		self.handlers.append(handler_func)


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
		options.page_load_strategy = 'eager'
		options.add_argument('--headless')
		options.add_argument(f"user-agent={userAgent}")
		self.driver = driver = webdriver.Chrome(options=options)
		driver.set_window_size(1000, 1080)

		# ad watcher
		watcher = self.watcher = AdWatcher(driver)
		watcher.add_handler(lambda: WeatherNews.close_ad(self.driver))
		watcher.start()


	def open(self):
		driver = self.driver
		driver.get("https://weathernews.jp/mountain/")
		self.wait = wait = WebDriverWait(driver, 3)
		try:
			wait.until(EC.visibility_of_element_located((By.ID, "map")))
		except:
			pass

		# zoom in
		self.zoom_in_map(3)
		self.move_map(-50,-50)
		self.zoom_in_map(3)
		self.move_map(-50,0)
		self.zoom_in_map(3)
		self.move_map(-100,100)
		#self.move_map(-100,-100)
		#self.move_map(-100,-80)
		#self.move_map(-100,0)
		#self.move_map(-50,0)

		# scroll down to find calendar
		self.scroll_until_visible("土")


	def zoom_in_map(self, times=3):
		print("zoom_in_map")
		driver = self.driver
		wait = self.wait
		zoom_in_button = wait.until(
			EC.presence_of_element_located((By.CSS_SELECTOR, "a.leaflet-control-zoom-in"))
		)

		#driver.execute_script("arguments[0].scrollIntoView(true);", zoom_in_button)
		try:
			driver.execute_script("arguments[0].scrollIntoView({block: 'nearest', inline: 'nearest'});", zoom_in_button)
		except:
			pass
		time.sleep(0.2)

		try:
			ActionChains(driver).move_to_element(zoom_in_button).perform()
		except:
			pass
		time.sleep(0.2)

		for _ in range(times):
			try:
				if zoom_in_button.is_displayed():
					try:
						zoom_in_button.click()
					except (ElementClickInterceptedException, ElementNotInteractableException):
						driver.execute_script("arguments[0].click();", zoom_in_button)

				time.sleep(0.5)
			except: # (TimeoutException, StaleElementReferenceException) as e:
				pass #print(f"Zoom in failed at attempt: {e}")
			break


	def move_map(self, x_offset, y_offset):
		print("move_map")
		driver = self.driver
		wait = self.wait
		map_element = None
		try:
			map_element = wait.until(EC.presence_of_element_located((By.ID, "map")))
		except:
			pass

		if map_element:
			try:
				actions = ActionChains(driver)
				actions.click_and_hold(map_element).move_by_offset(x_offset, y_offset).release().perform()
			except:
				pass
			time.sleep(0.1)
		else:
			print("Unable to find the map")

	def scroll_until_visible(self, wday):
		print("scroll_until_visible")
		driver = self.driver
		wait = self.wait
		body = None
		try:
			body = driver.find_element(By.TAG_NAME, "body")
		except:
			pass
		button = None
		max_try = 100
		try_count = 0
		while try_count<max_try:
			try:
				button = wait.until(EC.element_to_be_clickable((By.XPATH, f"//button[p/span[text()='{wday}']]")))
				# try to click (assume to receive exception)
				button.click()
				# not received case menas found it!
				time.sleep(0.1)
				return
			except:
				pass
			try:
				body.send_keys(Keys.ARROW_DOWN)
			except:
				pass
			time.sleep(0.1)
			try_count += 1


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

	def get_target_date_button(self, wday, target_date=None):
		button = None

		wait = self.wait

		xpaths = []
		xpaths.append( f"//button[p[contains(text(), '{wday}') or span[contains(text(), '{wday}')]]]")
		if target_date:
			xpaths.append( f"//button[p[contains(text(), '{target_date}') or span[contains(text(), '{target_date}')]]]")
		is_found = False
		for xpath in xpaths:
			try:
				buttons = wait.until(EC.presence_of_all_elements_located((By.XPATH, xpath)))
				for button in buttons:
					texts = button.text.strip().split(" ")
					for text in texts:
						text = text.strip()
						print(text)
						if text == wday or (target_date and text == target_date):
							button.click()
							time.sleep(0.1)
							print(f'found..{texts}:{text}')
							is_found = True
							break
			except:
				pass

		if is_found:
			return button
		else:
			return None

	def select_date_and_capture(self, wday, filename = None, target_date = None):
		wait = self.wait
		print(f"target wday={wday}, target_date={target_date}")

		# select wday
		button = self.get_target_date_button(wday, target_date)
		if not button:
			return False
		time.sleep(1)

		# get current wday and date
		date_text = None
		wday_text = None
		day_only = None
		if button:
			try:
				date_text = button.find_element(By.CSS_SELECTOR, ".week-item-text").get_attribute("innerText").strip()
				wday_text = button.find_element(By.CSS_SELECTOR, ".week-item-wday").text.strip()
				day_only = date_text.replace(wday_text, "").strip()
			except:
				pass
			print(f"Date: {day_only}, Week: {wday_text}")

		# save
		if not filename:
			if wday_text and wday_text in self.WEEK_FILENAME:
				filename = self.WEEK_FILENAME[wday_text]
			else:
				filename = "weather_map.png"

		map_element = None
		map_element = wait.until(EC.presence_of_element_located((By.ID, "map")))
		print(f"capture:{filename}")
		if map_element:
			map_element.screenshot(filename)
		else:
			self.cropped_capture(filename, 13*self.density, 220*self.density+self.offset_y, 568*self.density, 779*self.density+self.offset_y)
			#self.cropped_capture(filename, 26,				253+198+78, 	  1134+10,			1200+198+78*3)
		return True

	def get_weathers(self, requests):
		success = True
		for wday, filename in requests.items():
			success = success and self.select_date_and_capture(wday, filename)
		return success

	def get_weathers_map(self, wdays):
		success = True
		for wday in wdays:
			success = success and self.select_date_and_capture(wday)
		return success

	def close(self):
		if self.watcher:
			self.watcher.stop()
			self.watcher = None
		if self.driver:
			self.wait = None
			self.driver.quit()
			self.driver = None

	# for lambda (static func)
	def close_ad(driver):
		print("Try to close Ad")
		try:
			driver.back()
			time.sleep(0.5)
			driver.switch_to.default_content()
			time.sleep(0.5)
		except:
			pass
		return

		try:
			iframes = driver.find_elements(By.TAG_NAME, "iframe")
			for iframe in iframes:
				driver.switch_to.frame(iframe)
				try:
					close_button = driver.find_element(By.CSS_SELECTOR, "div[aria-label='Close']")
					close_button.click()
					print("Closed ad.")
					driver.switch_to.default_content()
					return
				except:
					driver.switch_to.default_content()
					continue
		except:
			pass

		try:
			close_button = driver.find_element(By.CSS_SELECTOR, "div[aria-label='Close']")
			close_button.click()
			print("Closed ad (no iframe).")
		except:
			pass
		driver.switch_to.default_content()


if __name__=="__main__":
	parser = argparse.ArgumentParser(description='Parse command line options.')
	parser.add_argument('args', nargs='*', help='mountain name such as 富士山')
	parser.add_argument('-d', '--date', action='store', default='', help='specify date e.g. 2/14,2/16-2/17')
	parser.add_argument('-dw', '--dateweekend', action='store_true', help='specify if weekend (Saturday and Sunday)')
	args = parser.parse_args()

	specifiedDates = TenkuraFilterUtil.getListOfDates( args.date )
	if args.dateweekend:
		weekEndDates = TenkuraFilterUtil.getWeekEndYYMMDD( datetime.datetime.now(), False )
		specifiedDates.extend(weekEndDates)
		specifiedDates = list(set(filter(None,specifiedDates)))
		specifiedDates.sort(key=TenkuraFilterUtil.dateSortUtil)

	target_dates = []
	for _day in specifiedDates:
		pos = _day.rfind("/")
		if pos!=-1:
			target_dates.append( str(int(_day[pos+1:])) )

	news = WeatherNews()
	news.open()
	#news.get_weathers( {"土":"saturday.png", "日":"sunday.png"} )
	sucess = news.get_weathers_map(target_dates)
	news.close()
	if not sucess:
		exit(-1)
