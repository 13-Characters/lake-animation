# Lake Wallpaper

Generates a wallpaper of a lake based on the current time and user-provided location.
The wallpaper is based off a wallpaper on r/wallpapers made by u/Tomu_Ozawa, which was based off of [this Reddit post](https://www.reddit.com/r/EarthPorn/comments/3ihsre/my_favourite_shot_from_yellowstone_taken_at_bay/).

## Demo:
![Demo](./test.mp4)

## Usage:
The instructions on how to set up the wallpaper differ depending on which operating system you use. Instructions for Linux can be found below.
The script `wallpaper.py` generates an SVG file based on the current time (if time is not provided) and user-provided location to `lake.svg`.
To generate an SVG file, run the command
```
python wallpaper.py $LATITUDE $LONGITUDE $UNIX_TIME
```
where `$LATITUDE` and `$LONGITUDE` are the latitude and longitude of the user-provided location, and `$UNIX_TIME` is an optional parameter for the number of seconds since the Unix Epoch.

For example, if you wanted to get the wallpaper for the current time in Paris, France, you would run
```
python wallpaper.py 48.8737 2.2950
```
and to get the wallpaper for January 1st, 1970 in Paris, France you would run
```
python wallpaper.py 48.8737 2.2950 0
```
### Linux:
The instructions for how to set up the wallpaper differ depending on
which window manager you are using this from. Regardless of which window manager you are using, you should install `resvg`. If you are on a Debian-based distro, you can do so by running
```
sudo apt update
sudo apt install resvg
```
### Linux (i3):
If you are using the i3 window manager then you can use [feh](https://github.com/derf/feh) to change the wallpaper. Running the following script after login will change the wallpaper every ten seconds:
```
cd $(dirname "$0")
while [ 1 = 1 ]; do
  python3 wallpaper.py $LATITUDE $LONGITUDE
  resvg lake.svg bg.png
  feh --bg-scale --zoom fill bg.png
  sleep 10
done
```
replace `$LATITUDE` and `$LONGITUDE` with the location that you wish to provide.
### Linux (Wayland):
If you are using a tiling window manager based on Wayland then you can use [awww](https://codeberg.org/LGFae/awww) to change the wallpaper. (I am currently running v0.9.5, so these instructions might not work on the latest version) Running the following script after login will change the wallpaper every ten seconds:
```
cd "$(dirname "$0")"
python3 changer.py $LATITUDE $LONGITUDE
```
