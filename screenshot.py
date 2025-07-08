# Made in order to screenshot the html file to make a wallpaper
from datetime import datetime
import math
from pathlib import Path
from playwright.sync_api import sync_playwright

LATITUDE = 33.646
LONGITUDE = -117.843
now = math.floor(datetime.now().timestamp())
url = Path('lake.html').absolute().as_uri()
url += f"?LATITUDE={LATITUDE}&LONGITUDE={LONGITUDE}&STARTING_TIME={now}"

def run(playwright):
  firefox = playwright.firefox
  browser = firefox.launch()
  page = browser.new_page()
  page.set_viewport_size({"width": 3840, "height": 2160})
  page.goto(url)
  page.screenshot(path="lake.png")
  browser.close()

with sync_playwright() as playwright:
    run(playwright)