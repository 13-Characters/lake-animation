import sys
from datetime import datetime
import math
import sky_utils
import json
import xml.dom.minidom
from math import pow, pi, sin, cos, tan

HORIZON_Y = 1420
IMAGE_WIDTH = 3840
IMAGE_HEIGHT = 2560
HORIZONTAL_FOV = math.pi / 3
CAMERA_AZIMUTH = math.pi * 1.45

now = math.floor(datetime.now().timestamp()) if len(sys.argv) <= 3 else float(sys.argv[3])

with open("star.xml") as svg_file:
    star_xml = xml.dom.minidom.parse(svg_file)

with open("sun.xml") as svg_file:
  sun_xml = xml.dom.minidom.parse(svg_file)

with open("input.svg") as svg_file:
  sky_svg = xml.dom.minidom.parse(svg_file)

svg_element = sky_svg.childNodes[1]
star_image = star_xml.firstChild
sun = sun_xml.firstChild

def place_sun(x, y):
  sun_copy = sun.cloneNode(True)
  sun_copy.setAttribute("transform", f"translate({x} {y})")
  svg_element.appendChild(sun_copy)

def place_star(x, y, mag):
  star_copy = star_image.cloneNode(True)
  scale = 5 * pow(1.5, -mag)
  star_copy.setAttribute("transform", f"translate({x} {y}) scale({scale})")
  svg_element.appendChild(star_copy)

def save_svg():
  with open("output.svg", "w") as output:
    svg_element.writexml(output, indent="\t", newl="\n")

# x-axis is towards the direction the camera is facing, z-axis is up-down
def az_alt_cartesian(azimuth, altitude):
  i = (azimuth - CAMERA_AZIMUTH) % (2*pi)
  x = cos(i) * cos(altitude)
  y = sin(i) * cos(altitude)
  z = sin(altitude)
  return (x, y, z)


def az_alt_to_XY(azimuth, altitude):
  x, y, z = az_alt_cartesian(azimuth, altitude)
  if x > 0:
    screen_x = y/x
    screen_y = z/x
  else: return None
  scale_factor = tan(HORIZONTAL_FOV) * (IMAGE_WIDTH / 2)
  screen_x *= scale_factor
  screen_y *= scale_factor
  screen_x += (IMAGE_WIDTH / 2)
  screen_y += HORIZON_Y
  if (-200 < screen_x < IMAGE_WIDTH + 200) and (-200 < screen_y < IMAGE_HEIGHT + 200):
    return (screen_x, screen_y)
  return None

if __name__ == "__main__":
  LATITUDE = float(sys.argv[1])
  LONGITUDE = float(sys.argv[2])
  rotation = sky_utils.get_rotation(now, LONGITUDE)
  sun_pos = sky_utils.get_sun_coords(now)
  sun_az_alt = sky_utils.equatorial_to_az_alt(*sun_pos, rotation, LATITUDE)
  sun_XY = az_alt_to_XY(*sun_az_alt)
  if sun_XY:
    place_sun(*sun_XY)
  if sun_az_alt[1] < 0:
    star_data = json.load(open("star_data.json"))
    for star in star_data:
      star_az_alt = sky_utils.equatorial_to_az_alt(float(star["RA"]), float(star["DEC"]), rotation, LATITUDE)
      star_XY = az_alt_to_XY(*star_az_alt)
      if star_XY:
        place_star(star_XY[0], star_XY[1], float(star["MAG"]))
  save_svg()