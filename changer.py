# This script needs swww and resvg on Linux to work
import wallpaper
from time import sleep, time, process_time
import subprocess
import sys

if len(sys.argv) <= 2:
    print("Not enough arguments specified, you must specify longitude and latitude")
    raise Exception

while True:
    print(f"[{process_time()}] Start loop")
    try:
        LATITUDE = float(sys.argv[1])
        LONGITUDE = float(sys.argv[2])
    except:
        print("Arguments must be longitude and latitude coordinates")
        raise ValueError
    svg_data = wallpaper.render(LATITUDE, LONGITUDE, int(time()))
    svg_data.seek(0)
    svg_string = svg_data.read()
    print(f"[{process_time()}] Created svg")
    svg_string = bytes(svg_string, encoding='utf-8')
    subprocess.run("resvg - /dev/stdout --resources-dir . | swww img -t none -", shell=True, input=svg_string)
    print(f"[{process_time()}] Created png")
    sleep(10)
    wallpaper.reload()
