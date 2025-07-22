import sys
from datetime import datetime
import math
import sky_utils
import json
import xml.dom.minidom
from math import pow, pi, sin, cos, tan
import cairosvg

HORIZON_Y = 1420
IMAGE_WIDTH = 3840
IMAGE_HEIGHT = 2560
HORIZONTAL_FOV = math.pi / 3
CAMERA_AZIMUTH = math.pi * 1.45
EARTH_ROTATION_PERIOD = 86164.098904

now = math.floor(datetime.now().timestamp()) if len(sys.argv) <= 3 else float(sys.argv[3])

with open("star.xml") as xml_file:
    star_xml = xml.dom.minidom.parse(xml_file)

with open("sun.xml") as xml_file:
  sun_xml = xml.dom.minidom.parse(xml_file)

with open("clouds.xml") as xml_file:
  clouds_xml = xml.dom.minidom.parse(xml_file)

with open("input.svg") as svg_file:
  sky_svg = xml.dom.minidom.parse(svg_file)

svg_element = sky_svg.childNodes[1]
star_image = star_xml.firstChild
sun = sun_xml.firstChild
clouds = clouds_xml.firstChild

def get_sun_color(sun_alt):
  daytime = ((255, 255, 255), (255, 255, 255))
  sunset = ((255, 180, 104), (255, 173, 91))
  if sun_alt > 0.08 * math.pi:
    return daytime
  if sun_alt < 0.02 * math.pi:
    return sunset
  t = (sun_alt - 0.02*math.pi) / (0.08*math.pi - 0.02*math.pi)
  result = [0, 0]
  for i in [0, 1]:
    result[i] = color_blend(sunset[i], daytime[i], t)
  return result

def place_sun(x, y, sun_color, sun_glow_color):
  sun_copy = sun.cloneNode(True)
  sun_copy.setAttribute("transform", f"translate({x} {y})")
  for i, element in enumerate(sun_copy.childNodes):
    if type(element) != xml.dom.minidom.Element:
      continue
    if i < 4:
      element.setAttribute("style", f"display:inline;opacity:1;fill:{color_to_hex_value(sun_glow_color)};fill-opacity:0.0538922;stroke:none;")
    else:
      element.setAttribute("style", f"display:inline;fill:{color_to_hex_value(sun_color)};fill-opacity:1;stroke:none;")
  svg_element.appendChild(sun_copy)

def place_star(x, y, scale):
  star_copy = star_image.cloneNode(True)
  star_copy.setAttribute("transform", f"translate({x} {y}) scale({scale})")
  svg_element.appendChild(star_copy)

def place_clouds(x):
  clouds_copy = clouds.cloneNode(True)
  elements = [element for element in clouds_copy.childNodes if type(element) == xml.dom.minidom.Element]
  pattern = elements[0]
  rect = elements[1]
  svg_element.appendChild(pattern)
  rect.setAttribute("transform", f"translate({x} 667) scale(3.77913)")
  svg_element.appendChild(rect)

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
    screen_y = -z/x
  else: return None
  scale_factor = tan(HORIZONTAL_FOV) * (IMAGE_WIDTH / 2)
  screen_x *= scale_factor
  screen_y *= scale_factor
  screen_x += (IMAGE_WIDTH / 2)
  screen_y += HORIZON_Y
  if (-200 < screen_x < IMAGE_WIDTH + 200) and (-200 < screen_y < IMAGE_HEIGHT + 200):
    return (screen_x, screen_y)
  return None

def fade_out_function(altitude):
  threshold = -math.pi * 0.12
  if altitude < threshold:
    return 1
  if altitude > 0:
    return 0
  if altitude < 0:
    return -((altitude/threshold - 1)**2) + 1
  
def color_blend(color1, color2, t):
  if not (0 <= t <= 1):
    print("t is not between 0 and 1")
    raise ValueError
  color1 = list(map(lambda x: x/255, color1))
  color2 = list(map(lambda x: x/255, color2))
  color1 = list(map(lambda x: x**(2.2), color1))
  color2 = list(map(lambda x: x**(2.2), color2))
  blend = [(1 - t)*a + t*b for a,b in zip(color1, color2)]
  blend = list(map(lambda x: x**(1/2.2), blend))
  blend = list(map(lambda x: x*255, blend))
  return blend

def color_to_hex_value(color):
  result = "#"
  for channel in color:
    result += f"{round(channel):02x}"
  return result

# Used to blend between the sunrise/sunset gradients
def azimuth_blend(azimuth):
  threshold = math.pi / 9
  x = abs((azimuth - math.pi/2) % (2*math.pi))
  if (x < threshold or x > 2*math.pi - threshold):
    return 0
  if (abs(x - math.pi) < threshold):
    return 1
  if (x < math.pi):
    return (x - threshold) / (math.pi - 2*threshold)
  else:
    return (2*math.pi - x - threshold) / (math.pi - 2*threshold)

def update_sky_colors(sun_azimuth, sun_altitude):
  daytime_colors = {"top": (0x4c, 0x7c, 0xd2), "bottom": (0xad, 0xc9, 0xf1)}
  sunset_colors = {"top": (0x31, 0x33, 0x59), "bottom": (0xe1, 0x6c, 0x37)}
  sunrise_colors = {"top": (0x31, 0x33, 0x59), "bottom": (0xc6, 0x62, 0x91)}
  dusk_colors = {"top": (0x20, 0x0b, 0x34), "bottom": (0x7f, 0x19, 0x4c)}
  dawn_colors = {"top": (0x20, 0x0b, 0x34), "bottom": (0x37, 0x28, 0x58)}
  night_colors = {"top": (0x13, 0x0d, 0x19), "bottom": (0x2b, 0x15, 0x2f)}
  stops = svg_element.firstChild.firstChild.childNodes
  # Altitudes for when the transition between daytime and sunset colors begin and end
  daytime_to_sunset_start = {"top": math.pi*0.16, "bottom": math.pi*0.25} # Seems more natural if bottom changes before top
  daytime_to_sunset_end = {"top": math.pi * 0.08, "bottom": math.pi * 0.08}
  sunset_to_twilight_start = {"top": 0, "bottom": 0}
  sunset_to_twilight_end = {"top": -math.pi * 0.075, "bottom": -math.pi*0.04}
  twilight_to_night_start = {"top": -math.pi * 0.08, "bottom": -math.pi * 0.08}
  twilight_to_night_end = {"top": -math.pi * 0.09, "bottom": -math.pi * 0.12}
  if (sun_altitude > 0):
    for i, part in enumerate(["top", "bottom"]):
      t_altitude = (sun_altitude - daytime_to_sunset_end[part]) / (daytime_to_sunset_start[part] - daytime_to_sunset_end[part])
      t_altitude = max(0, min(t_altitude, 1)) # Make sure this is bounded between 0 and 1
      t_azimuth = azimuth_blend(sun_azimuth)
      # If only there were a general term for sunrise and sunset
      lowsun = color_blend(sunrise_colors[part], sunset_colors[part], t_azimuth)
      sky_color = color_blend(lowsun, daytime_colors[part], t_altitude)
      stops[i].setAttribute("style", f"stop-color:{color_to_hex_value(sky_color)};stop-opacity:1;")
  if (-0.08 * math.pi < sun_altitude <= 0):
    for i, part in enumerate(["top", "bottom"]):
      t_altitude = (sun_altitude - sunset_to_twilight_end[part]) / (sunset_to_twilight_start[part] - sunset_to_twilight_end[part])
      t_altitude = max(0, min(t_altitude, 1)) # Make sure this is bounded between 0 and 1
      t_azimuth = azimuth_blend(sun_azimuth)
      # If only there were a general term for sunrise and sunset
      lowsun = color_blend(sunrise_colors[part], sunset_colors[part], t_azimuth)
      twilight = color_blend(dawn_colors[part], dusk_colors[part], t_azimuth)
      sky_color = color_blend(twilight, lowsun, t_altitude)
      stops[i].setAttribute("style", f"stop-color:{color_to_hex_value(sky_color)};stop-opacity:1;")
  if (sun_altitude <= -0.08 * math.pi):
    for i, part in enumerate(["top", "bottom"]):
      t_altitude = (sun_altitude - twilight_to_night_end[part]) / (twilight_to_night_start[part] - twilight_to_night_end[part])
      t_altitude = max(0, min(t_altitude, 1)) # Make sure this is bounded between 0 and 1
      t_azimuth = azimuth_blend(sun_azimuth)
      # If only there were a general term for sunrise and sunset
      twilight = color_blend(dawn_colors[part], dusk_colors[part], t_azimuth)
      sky_color = color_blend(night_colors[part], twilight, t_altitude)
      stops[i].setAttribute("style", f"stop-color:{color_to_hex_value(sky_color)};stop-opacity:1;")


if __name__ == "__main__":
  LATITUDE = float(sys.argv[1])
  LONGITUDE = float(sys.argv[2])
  rotation = sky_utils.get_rotation(now, LONGITUDE)
  sun_pos = sky_utils.get_sun_coords(now)
  sun_az_alt = sky_utils.equatorial_to_az_alt(*sun_pos, rotation, LATITUDE)
  sun_XY = az_alt_to_XY(*sun_az_alt)
  sun_colors = get_sun_color(sun_az_alt[1])
  if sun_XY:
    place_sun(*sun_XY, *sun_colors)
  update_sky_colors(*sun_az_alt)
  
  if sun_az_alt[1] < 0:
    star_data = json.load(open("star_data.json"))
    for star in star_data:
      star_az_alt = sky_utils.equatorial_to_az_alt(float(star["RA"]), float(star["DEC"]), rotation, LATITUDE)
      star_XY = az_alt_to_XY(*star_az_alt)
      mag = float(star["MAG"])
      scale = (5 * pow(1.5, -mag)) - (6 * (1 - fade_out_function(sun_az_alt[1])))
      if star_XY and scale > 0:
        place_star(star_XY[0], star_XY[1], scale)

  cloud_x = -((now/80000 % 1)+0.5)*7203.4177
  place_clouds(cloud_x)
  
  save_svg()