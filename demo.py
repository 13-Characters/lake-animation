# Made to create a timelapse
import wallpaper
import resvg_py
from time import sleep, process_time
import subprocess
import sys

if len(sys.argv) <= 2:
    print("Not enough arguments specified, you must specify longitude and latitude")
    raise Exception

start_time = 1753599600
for i in range(0, 8640):
    subprocess.run(f"date -s @{start_time + 10*i}", shell=True)
    try:
        LATITUDE = float(sys.argv[1])
        LONGITUDE = float(sys.argv[2])
    except:
        print("Arguments must be longitude and latitude coordinates")
        raise ValueError
    svg_data = wallpaper.render(LATITUDE, LONGITUDE, start_time + 10*i)
    svg_data.seek(0)
    svg_string = svg_data.read()
    svg_string = bytes(svg_string, encoding='utf-8')
    subprocess.run("resvg - /dev/stdout --resources-dir . | swww img -t none -", shell=True, input=svg_string)
    subprocess.run(f"grim ./demo/{i:04}.png", shell=True)
    wallpaper.reload()
