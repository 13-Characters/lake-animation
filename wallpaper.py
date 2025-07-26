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

now = math.floor(datetime.now().timestamp())

with open("star.xml") as xml_file:
    star_xml = xml.dom.minidom.parse(xml_file)

with open("sun.xml") as xml_file:
  sun_xml = xml.dom.minidom.parse(xml_file)

with open("clouds.xml") as xml_file:
  clouds_xml = xml.dom.minidom.parse(xml_file)

with open("base.svg") as svg_file:
  base_svg = xml.dom.minidom.parse(svg_file)

svg_element = base_svg.childNodes[1]
star_image = star_xml.firstChild
sun = sun_xml.firstChild
clouds = clouds_xml.firstChild

def reload():
  global svg_element
  global base_svg
  with open("base.svg") as svg_file:
    base_svg = xml.dom.minidom.parse(svg_file)
  svg_element = base_svg.childNodes[1]


def color_blend(color1, color2, t):
  if not (0 <= t <= 1):
    print("t is not between 0 and 1")
    raise ValueError
  color1 = list(map(lambda x: x/255, color1))
  color2 = list(map(lambda x: x/255, color2))
  # color1 = list(map(lambda x: x**(2.2), color1))
  # color2 = list(map(lambda x: x**(2.2), color2))
  blend = [(1 - t)*a + t*b for a,b in zip(color1, color2)]
  # blend = list(map(lambda x: x**(1/2.2), blend))
  blend = list(map(lambda x: x*255, blend))
  return blend

def color_to_hex_value(color):
  result = "#"
  for channel in color:
    result += f"{round(channel):02x}"
  return result

def get_color(sun_azimuth, sun_altitude,
              eastcolor1=None, eastcolor2=None, 
              westcolor1=None, westcolor2=None,
              keyframe1=None, keyframe2=None):
  if not all([x != None for x in [eastcolor1, eastcolor2, westcolor1, westcolor2, keyframe1, keyframe2]]):
    raise ValueError
  t_altitude = (sun_altitude - keyframe2) / (keyframe1 - keyframe2)
  t_altitude = max(0, min(t_altitude, 1)) # Make sure this is bounded between 0 and 1
  t_azimuth = azimuth_blend(sun_azimuth)
  east = color_blend(eastcolor1, eastcolor2, t_altitude)
  west = color_blend(westcolor1, westcolor2, t_altitude)
  result = color_blend(east, west, t_azimuth)
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

def get_mountain_element():
  for element in svg_element.childNodes:
    if isinstance(element, xml.dom.minidom.Element):
      if element.hasAttribute("id") and element.getAttribute("id") == "mountains":
        return element
  return None

def get_reflection_element():
  for node in svg_element.childNodes:
    if isinstance(node, xml.dom.minidom.Element) and node.hasAttribute("id") and \
    node.getAttribute("id") == "reflection":
      return node
  return None

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
  svg_element.insertBefore(sun_copy, get_mountain_element())

def place_star(x, y, scale):
  star_copy = star_image.cloneNode(True)
  star_copy.setAttribute("transform", f"translate({x} {y}) scale({scale})")
  svg_element.insertBefore(star_copy, get_mountain_element())

def place_clouds(x, sun_azimuth, sun_altitude):
  daytime_color = (0xe6, 0xf8, 0xff)
  sunset_color = (0xe5, 0x8b, 0x3d)
  sunrise_color = (0xe5, 0x8b, 0x3d)
  dusk_color = (0x9a, 0x5c, 0x5c)
  dawn_color = (0x35, 0x36, 0x53)
  night_color = (0x1f, 0x0d, 0x1f)

  daytime_to_sunset_start = math.pi*0.22
  daytime_to_sunset_end = math.pi*0.08
  sunset_to_twilight_start = 0
  sunset_to_twilight_end = -math.pi*0.06
  twilight_to_night_start = -math.pi*0.08
  twilight_to_night_end = -math.pi*0.10
  clouds_copy = clouds.cloneNode(True)
  elements = [element for element in clouds_copy.childNodes if type(element) == xml.dom.minidom.Element]
  pattern = elements[0]
  rect = elements[1]
  svg_element.appendChild(pattern)
  rect.setAttribute("transform", f"translate({x} 667) scale(3.77913)")
  if (sun_altitude > 0):
    cloud_color = get_color(sun_azimuth=sun_azimuth, sun_altitude=sun_altitude,
                            eastcolor1=sunrise_color, eastcolor2=daytime_color,
                            westcolor1=sunset_color, westcolor2=daytime_color,
                            keyframe1=daytime_to_sunset_start, keyframe2=daytime_to_sunset_end)
  if (-0.08*math.pi < sun_altitude <= 0):
    cloud_color = get_color(sun_azimuth=sun_azimuth, sun_altitude=sun_altitude,
                            eastcolor1=dawn_color, eastcolor2=sunrise_color,
                            westcolor1=dusk_color, westcolor2=sunset_color,
                            keyframe1=sunset_to_twilight_start, keyframe2=sunset_to_twilight_end)
  if (sun_altitude <= -0.08*math.pi):
    cloud_color = get_color(sun_azimuth=sun_azimuth, sun_altitude=sun_altitude,
                            eastcolor1=night_color, eastcolor2=dawn_color,
                            westcolor1=night_color, westcolor2=dusk_color,
                            keyframe1=twilight_to_night_start, keyframe2=twilight_to_night_end)
  for element in pattern.childNodes[3].childNodes[1].childNodes:
    if element.nodeName == "path":
      element.setAttribute("style", f"display:inline;fill:{color_to_hex_value(cloud_color)};fill-opacity:1;stroke:none;")
  svg_element.insertBefore(rect, get_mountain_element())

def recolor_mountains(sun_azimuth, sun_altitude):
  daytime_colors = {"foreground": (0x66, 0x76, 0xa9), "background": (0x41, 0x48, 0x75)}
  sunset_colors = {"foreground": (0x8e, 0x42, 0x44), "background": (0x58, 0x2e, 0x46)}
  sunrise_colors = {"foreground": (0x99, 0x4d, 0x60), "background": (0x5f, 0x2f, 0x51)}
  dusk_colors = {"foreground": (0x4d, 0x13, 0x44), "background": (0x30, 0x11, 0x31)}
  dawn_colors = {"foreground": (0x27, 0x1d, 0x47), "background": (0x13, 0x13, 0x2d)}
  night_colors = {"foreground": (0x1b, 0x07, 0x1b), "background": (0x11, 0x0b, 0x16)}

  daytime_to_sunset_start = 0.20*math.pi
  daytime_to_sunset_end = 0.08*math.pi
  sunset_to_twilight_start = 0
  sunset_to_twilight_end = -0.06*math.pi
  twilight_to_night_start = -0.08*math.pi
  twilight_to_night_end = -0.10*math.pi

  if (sun_altitude > 0):
    foreground_color = get_color(sun_azimuth, sun_altitude,
                                 eastcolor1=sunrise_colors["foreground"], eastcolor2=daytime_colors["foreground"],
                                 westcolor1=sunset_colors["foreground"], westcolor2=daytime_colors["foreground"],
                                 keyframe1=daytime_to_sunset_start, keyframe2=daytime_to_sunset_end)
    background_color = get_color(sun_azimuth, sun_altitude,
                                 eastcolor1=sunrise_colors["background"], eastcolor2=daytime_colors["background"],
                                 westcolor1=sunset_colors["background"], westcolor2=daytime_colors["background"],
                                 keyframe1=daytime_to_sunset_start, keyframe2=daytime_to_sunset_end)
  if (-0.08*math.pi < sun_altitude <= 0):
    foreground_color = get_color(sun_azimuth, sun_altitude,
                                 eastcolor1=dawn_colors["foreground"], eastcolor2=sunrise_colors["foreground"],
                                 westcolor1=dusk_colors["foreground"], westcolor2=sunset_colors["foreground"],
                                 keyframe1=sunset_to_twilight_start, keyframe2=sunset_to_twilight_end)
    background_color = get_color(sun_azimuth, sun_altitude,
                                 eastcolor1=dawn_colors["background"], eastcolor2=sunrise_colors["background"],
                                 westcolor1=dusk_colors["background"], westcolor2=sunset_colors["background"],
                                 keyframe1=sunset_to_twilight_start, keyframe2=sunset_to_twilight_end)
  if (sun_altitude <= -0.08*math.pi):
    foreground_color = get_color(sun_azimuth, sun_altitude,
                                 eastcolor1=night_colors["foreground"], eastcolor2=dawn_colors["foreground"],
                                 westcolor1=night_colors["foreground"], westcolor2=dusk_colors["foreground"],
                                 keyframe1=twilight_to_night_start, keyframe2=twilight_to_night_end)
    background_color = get_color(sun_azimuth, sun_altitude,
                                 eastcolor1=night_colors["background"], eastcolor2=dawn_colors["background"],
                                 westcolor1=night_colors["background"], westcolor2=dusk_colors["background"],
                                 keyframe1=twilight_to_night_start, keyframe2=twilight_to_night_end)
  
  mountains = get_mountain_element()
  midground_color = color_blend(foreground_color, background_color, 0.5)
  for layer in mountains.childNodes:
    if layer.hasAttribute("id"):
      if layer.getAttribute("id") == "foreground":
        layer.setAttribute("style", f"display:inline;fill:{color_to_hex_value(foreground_color)};fill-opacity:1;stroke:none;")
      if layer.getAttribute("id") == "midground":
        layer.setAttribute("style", f"display:inline;fill:{color_to_hex_value(midground_color)};fill-opacity:1;stroke:none;")
      if layer.getAttribute("id") == "background":
        layer.setAttribute("style", f"display:inline;fill:{color_to_hex_value(background_color)};fill-opacity:1;stroke:none;")

def recolor_islands(sun_azimuth, sun_altitude):
  daytime_colors = {"background": (0x35, 0x3a, 0x65), "foreground": (0x20, 0x29, 0x3c)}
  sunset_colors = {"background": (0x3f, 0x2a, 0x49), "foreground": (0x26, 0x20, 0x3c)}
  sunrise_colors = {"background": (0x3f, 0x2a, 0x49), "foreground": (0x26, 0x20, 0x3c)}
  dusk_colors = {"background": (0x16, 0x13, 0x27), "foreground": (0x0d, 0x0d, 0x1a)}
  dawn_colors = {"background": (0x16, 0x13, 0x27), "foreground": (0x0d, 0x0d, 0x1a)}
  night_colors = {"background": (0x0b, 0x0b, 0x0f), "foreground": (0x05, 0x05, 0x08)}

  daytime_to_sunset_start = 0.20*math.pi
  daytime_to_sunset_end = 0.08*math.pi
  sunset_to_twilight_start = 0
  sunset_to_twilight_end = -0.06*math.pi
  twilight_to_night_start = -0.08*math.pi
  twilight_to_night_end = -0.10*math.pi

  background_island, foreground_island = None, None
  background_island_reflection, foreground_island_reflection = None, None
  for node in svg_element.childNodes:
    if (isinstance(node, xml.dom.minidom.Element) and node.hasAttribute("id")):
      if node.getAttribute("id") == "background-island":
        background_island = node
      if node.getAttribute("id") == "foreground-island":
        foreground_island = node
  reflection = get_reflection_element()
  if not reflection:
    raise Exception
  for node in svg_element.childNodes:
    if (isinstance(node, xml.dom.minidom.Element) and node.hasAttribute("id")):
      if node.getAttribute("id") == "background-island":
        background_island = node
      if node.getAttribute("id") == "foreground-island":
        foreground_island = node
  for node in reflection.childNodes:
    if (isinstance(node, xml.dom.minidom.Element) and node.hasAttribute("id")):
      if node.getAttribute("id") == "background-island-reflection":
        background_island_reflection = node
      if node.getAttribute("id") == "foreground-island-reflection":
        foreground_island_reflection = node
  if not all([background_island, foreground_island, 
              background_island_reflection, foreground_island_reflection]):
    raise Exception
  if (sun_altitude > 0):
    foreground_color = get_color(sun_azimuth, sun_altitude,
                                 eastcolor1=sunrise_colors["foreground"], eastcolor2=daytime_colors["foreground"],
                                 westcolor1=sunset_colors["foreground"], westcolor2=daytime_colors["foreground"],
                                 keyframe1=daytime_to_sunset_start, keyframe2=daytime_to_sunset_end)
    background_color = get_color(sun_azimuth, sun_altitude,
                                 eastcolor1=sunrise_colors["background"], eastcolor2=daytime_colors["background"],
                                 westcolor1=sunset_colors["background"], westcolor2=daytime_colors["background"],
                                 keyframe1=daytime_to_sunset_start, keyframe2=daytime_to_sunset_end)
  if (-0.08*math.pi < sun_altitude <= 0):
    foreground_color = get_color(sun_azimuth, sun_altitude,
                                 eastcolor1=dawn_colors["foreground"], eastcolor2=sunrise_colors["foreground"],
                                 westcolor1=dusk_colors["foreground"], westcolor2=sunset_colors["foreground"],
                                 keyframe1=sunset_to_twilight_start, keyframe2=sunset_to_twilight_end)
    background_color = get_color(sun_azimuth, sun_altitude,
                                 eastcolor1=dawn_colors["background"], eastcolor2=sunrise_colors["background"],
                                 westcolor1=dusk_colors["background"], westcolor2=sunset_colors["background"],
                                 keyframe1=sunset_to_twilight_start, keyframe2=sunset_to_twilight_end)
  if (sun_altitude <= -0.08*math.pi):
    foreground_color = get_color(sun_azimuth, sun_altitude,
                                 eastcolor1=night_colors["foreground"], eastcolor2=dawn_colors["foreground"],
                                 westcolor1=night_colors["foreground"], westcolor2=dusk_colors["foreground"],
                                 keyframe1=twilight_to_night_start, keyframe2=twilight_to_night_end)
    background_color = get_color(sun_azimuth, sun_altitude,
                                 eastcolor1=night_colors["background"], eastcolor2=dawn_colors["background"],
                                 westcolor1=night_colors["background"], westcolor2=dusk_colors["background"],
                                 keyframe1=twilight_to_night_start, keyframe2=twilight_to_night_end)
  background_island.setAttribute("style", f"display:inline;opacity:1;fill:{color_to_hex_value(background_color)};fill-opacity:1;stroke:none;")
  foreground_island.setAttribute("style", f"display:inline;opacity:1;fill:{color_to_hex_value(foreground_color)};fill-opacity:1;stroke:none;")
  background_island_reflection.setAttribute("style", f"display:inline;opacity:1;fill:{color_to_hex_value(background_color)};fill-opacity:1;stroke:none;")
  foreground_island_reflection.setAttribute("style", f"display:inline;opacity:1;fill:{color_to_hex_value(foreground_color)};fill-opacity:1;stroke:none;")

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

def duck_opacity(altitude):
  threshold = -2/27 * math.pi
  if altitude > 0:
    return 1
  else:
    return max(0, 1 - (altitude / threshold))

def change_duck_opacity(altitude):
  opacity = duck_opacity(altitude)
  ducks = None
  duck_reflection = None
  reflection = get_reflection_element()
  for node in svg_element.childNodes:
    if isinstance(node, xml.dom.minidom.Element) and node.hasAttribute("id"):
      if node.getAttribute("id") == "ducks":
        ducks = node
  for node in reflection.childNodes:
    if isinstance(node, xml.dom.minidom.Element) and node.hasAttribute("id"):
      if node.getAttribute("id") == "duck-reflection":
        duck_reflection = node
  if not all([ducks, duck_reflection]):
    raise Exception
  ducks.setAttribute("style", f"display:inline;fill:#16141f;fill-opacity:{opacity};stroke:none;")
  duck_reflection.setAttribute("style", f"display:inline;opacity:{opacity};fill:#16141f;fill-opacity:1;stroke:none;")

def recolor_sky(sun_azimuth, sun_altitude):
  sky_stops = svg_element.firstChild.firstChild.childNodes
  reflection_stops = svg_element.firstChild.childNodes[3].childNodes

  daytime_colors = {"top": (0x4c, 0x7c, 0xd2), "bottom": (0xad, 0xc9, 0xf1),
                    "top_reflection": (0x8d, 0x9f, 0xc2), "bottom_reflection": (0x5a, 0x75, 0xb2)}
  sunset_colors = {"top": (0x31, 0x33, 0x59), "bottom": (0xe1, 0x6c, 0x37),
                   "top_reflection": (0xbb, 0x6a, 0x5d), "bottom_reflection": (0x5c, 0x48, 0x6d)}
  sunrise_colors = {"top": (0x31, 0x33, 0x59), "bottom": (0xc6, 0x62, 0x91),
                    "top_reflection":(0xc3, 0x66, 0x85), "bottom_reflection": (0x5c, 0x48, 0x6d)}
  dusk_colors = {"top": (0x20, 0x0b, 0x34), "bottom": (0x7f, 0x19, 0x4c),
                 "top_reflection": (0x61, 0x32, 0x46), "bottom_reflection": (0x21, 0x1a, 0x25)}
  dawn_colors = {"top": (0x20, 0x0b, 0x34), "bottom": (0x37, 0x28, 0x58),
                 "top_reflection": (0x35, 0x2c, 0x54), "bottom_reflection": (0x21, 0x1a, 0x25)}
  night_colors = {"top": (0x13, 0x0d, 0x19), "bottom": (0x2b, 0x15, 0x2f),
                  "top_reflection":(0x2b, 0x14, 0x2b), "bottom_reflection": (0x08, 0x06, 0x08)}
  # Altitudes for when the transition between daytime and sunset colors begin and end
  daytime_to_sunset_start = {"top": math.pi*0.16, "bottom": math.pi*0.25} # Seems more natural if bottom changes before top
  daytime_to_sunset_end = {"top": math.pi * 0.08, "bottom": math.pi * 0.08}
  sunset_to_twilight_start = {"top": 0, "bottom": 0}
  sunset_to_twilight_end = {"top": -math.pi * 0.075, "bottom": -math.pi*0.04}
  twilight_to_night_start = {"top": -math.pi * 0.08, "bottom": -math.pi * 0.08}
  twilight_to_night_end = {"top": -math.pi * 0.09, "bottom": -math.pi * 0.12}
  def x(word): # In order to account for the reflection being different
    if word == "bottom":
      return "top"
    if word == "top":
      return "bottom"
    return None
  for i, part in enumerate(["top", "bottom"]):
    if (sun_altitude > 0):
      sky_color = get_color(sun_azimuth, sun_altitude, 
                            eastcolor1=sunrise_colors[part], eastcolor2=daytime_colors[part], 
                            westcolor1=sunset_colors[part], westcolor2=daytime_colors[part], 
                            keyframe1=daytime_to_sunset_start[part], keyframe2=daytime_to_sunset_end[part])
      reflection_color = get_color(sun_azimuth, sun_altitude, 
                            eastcolor1=sunrise_colors[part + "_reflection"], eastcolor2=daytime_colors[part + "_reflection"], 
                            westcolor1=sunset_colors[part + "_reflection"], westcolor2=daytime_colors[part + "_reflection"], 
                            keyframe1=daytime_to_sunset_start[x(part)], keyframe2=daytime_to_sunset_end[x(part)])
    if (-0.08 * math.pi < sun_altitude <= 0):
      sky_color = get_color(sun_azimuth, sun_altitude,
                            eastcolor1=dawn_colors[part], eastcolor2=sunrise_colors[part], 
                            westcolor1=dusk_colors[part], westcolor2=sunset_colors[part], 
                            keyframe1=sunset_to_twilight_start[part], keyframe2=sunset_to_twilight_end[part])
      reflection_color = get_color(sun_azimuth, sun_altitude,
                            eastcolor1=dawn_colors[part + "_reflection"], eastcolor2=sunrise_colors[part + "_reflection"], 
                            westcolor1=dusk_colors[part + "_reflection"], westcolor2=sunset_colors[part + "_reflection"], 
                            keyframe1=sunset_to_twilight_start[x(part)], keyframe2=sunset_to_twilight_end[x(part)])
    if (sun_altitude <= -0.08 * math.pi):
      sky_color = get_color(sun_azimuth, sun_altitude, 
                            eastcolor1=night_colors[part], eastcolor2=dawn_colors[part],
                            westcolor1=night_colors[part], westcolor2=dusk_colors[part], 
                            keyframe1=twilight_to_night_start[part], keyframe2=twilight_to_night_end[part])
      reflection_color = get_color(sun_azimuth, sun_altitude, 
                            eastcolor1=night_colors[part + "_reflection"], eastcolor2=dawn_colors[part + "_reflection"],
                            westcolor1=night_colors[part + "_reflection"], westcolor2=dusk_colors[part + "_reflection"], 
                            keyframe1=twilight_to_night_start[x(part)], keyframe2=twilight_to_night_end[x(part)])
    sky_stops[i].setAttribute("style", f"stop-color:{color_to_hex_value(sky_color)};stop-opacity:1;")
    reflection_stops[i].setAttribute("style", f"stop-color:{color_to_hex_value(reflection_color)};stop-opacity:1;")

def save_svg():
  with open("output.svg", "w") as output:
    svg_element.writexml(output, indent="\t", newl="\n")

def render(filename, LATITUDE, LONGITUDE, time):
  rotation = sky_utils.get_rotation(time, LONGITUDE)

  sun_pos = sky_utils.get_sun_coords(time)
  sun_az_alt = sky_utils.equatorial_to_az_alt(*sun_pos, rotation, LATITUDE)
  sun_XY = az_alt_to_XY(*sun_az_alt)
  sun_colors = get_sun_color(sun_az_alt[1])
  if sun_XY:
    place_sun(*sun_XY, *sun_colors)
  recolor_sky(*sun_az_alt)

  if sun_az_alt[1] < 0:
    star_data = json.load(open("star_data.json"))
    for star in star_data:
      star_az_alt = sky_utils.equatorial_to_az_alt(float(star["RA"]), float(star["DEC"]), rotation, LATITUDE)
      star_XY = az_alt_to_XY(*star_az_alt)
      mag = float(star["MAG"])
      scale = (5 * pow(1.5, -mag)) - (6 * (1 - fade_out_function(sun_az_alt[1])))
      if star_XY and scale > 0.4:
        place_star(star_XY[0], star_XY[1], scale)

  cloud_x = -((time/80000 % 1)+0.5)*7203.4177
  place_clouds(cloud_x, *sun_az_alt)

  recolor_mountains(*sun_az_alt)

  recolor_islands(*sun_az_alt)

  change_duck_opacity(sun_az_alt[1])

  save_svg()
  cairosvg.svg2png(url="./output.svg", write_to=f"./{filename}.png")

if __name__ == "__main__":
  LATITUDE = float(sys.argv[1])
  LONGITUDE = float(sys.argv[2])
  if len(sys.argv) > 3:
     now = float(sys.argv[3])
  render("lake", LATITUDE, LONGITUDE, now)
