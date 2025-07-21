'''
Used for calculating positions of celestial bodies in the sky, as well as converting between
different spherical coordinate systems.
'''
import numpy as np

'''Takes in the right ascension and declination in radians as parameters.
Outputs a vector with norm 1 in Cartesian coordinates,
with the x-axis being RA=12h on the equator, the y-axis being RA=6h on the equator,
and the z-axis being the north celestial pole.'''
def equatorial_cartesian_coordinates(ra, dec):
  i = (ra - np.pi/2) % (2*np.pi) # needed so i=0 corresponds to the x-axis 
  x = np.cos(i) * np.cos(dec)
  y = np.sin(i) * np.cos(dec)
  z = np.sin(dec)
  return (x, y, z)
  
'''Takes in a UNIX timestamp, 
and returns the right ascension and declination of the Sun at the given moment.'''
def get_sun_coords(time):
  n = (time-946728000) / 86400 # Number of days since January 1, 2000 at 12:00 GMT
  L = 4.89495 + 0.017202792*n
  g = 6.24004 + 0.017201970*n
  k = L + 0.03342*np.sin(g) + 0.00034*np.sin(2*g)
  j = 23.439*np.pi/180
  ra = np.atan2(np.cos(j)*np.cos(k), np.cos(k))
  dec = np.asin(np.sin(j)*np.sin(k))
  return (ra, dec)

'''The right ascension and declination of an object are the first two parameters.
"Rotation" is the right ascension of the zenith, in radians'''
def equatorial_to_az_alt(ra, dec, rotation, latitude):
  # Rotates about the z-axis
  rot_matrix_1 = np.array(
    [[np.cos(rotation), np.sin(rotation), 0], 
     [-np.sin(rotation), np.cos(rotation), 0], 
     [0, 0, 1]]
  )
  a = np.pi/2 - latitude
  rot_matrix_2 = np.array(
    [[1, 0, 0], 
     [0, np.cos(a), np.sin(a)], 
     [0, -np.sin(a), np.cos(a)]]
  )
  coords = np.array(equatorial_cartesian_coordinates(ra, dec))
  coords = np.matmul(rot_matrix_1, coords.T).T
  coords = np.matmul(rot_matrix_2, coords.T).T