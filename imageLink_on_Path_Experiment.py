#!/usr/bin/env python3

#
# This was written to show how to use a couple of routines
# modified for Charlie Figura
#
# Ken Sturrock
# August 03, 2018
#

from library.PySkyX_ks import *

import time
import sys
import os


# You can use takeImage or CLS.
#
# Anything that generates an image.
#
# If you are using the simulator, be aware that not
# every location solves reliably with the DSS images.
#
# Thuban is usually a reliable solver assuming the simulated camera's
# FOV is big enough. Like 1200x1000 or some such.
i
print("")
print("Taking an image at the current location.")
print("")

takeImage("Imager", "1", "0", "0")


# This uses a new routine to extract the path of the current active
# imaging camera image.

print("")
print("Getting the path of that image.")
print("")

imgPath = getActiveImagePath()

# You would then do something magic here which changes the name 
# of the file.
#
# In the real world. you wouldn't just rename, you would run your
# an external routine that will create a new path name.
# 
# You'd then have to figure out how to get the new path
# so that you end up with a variable that holds the new
# image path name that you want to feed into the getStatsPath 
# routine.

print("")
print("We are renaming the file by adding .garbage to the end as an experiment.")
print("")

newPath = imgPath + ".garbage"
os.rename(imgPath, newPath)


# This calls the other new routine which runs an Image Link
# and prints statistics on the specified file. It is now fixed
# so that id doubles the backslash so JS doesn't think it is a
# special character.

print("")
print("We will now try to pull statistics on that renamed image file.")
print("")

getStatsPath(newPath)



