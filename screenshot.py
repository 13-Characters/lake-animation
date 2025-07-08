# Made in order to screenshot the html file to make a wallpaper
from datetime import datetime
import math
from pathlib import Path
from playwright.sync_api import sync_playwright
import sys

LATITUDE = sys.argv[0]
LONGITUDE = sys.argv[1]
now = math.floor(datetime.now().timestamp())
p = Path(__file__).parent
url = (p / "lake.html").as_uri()
url += f"?LATITUDE={LATITUDE}&LONGITUDE={LONGITUDE}&STARTING_TIME={now}"

def run(playwright):
  browser = playwright.chromium.launch()
  ctx = browser.new_context()
  page = ctx.new_page()
  page.set_viewport_size({"width": 3840, "height": 2160})
  page.goto(url)
  page.screenshot(path=(p / "lake.png"))
  browser.close()

with sync_playwright() as playwright:
    run(playwright)

from sys import platform
if platform in ["win32", "cygwin"]:
   import ctypes
   import os
   ctypes.windll.user32.SystemParametersInfoW(20, 0, os.path.abspath(p / "lake.png"), 3)