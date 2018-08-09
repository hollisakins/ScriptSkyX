#!/usr/bin/env python3
#
# Run an automated session on SkyX.
#
# Syntax and functions are almost the same as the older Bash-based run_target script.
#
#       ./run_target-2 m51 5x300 5x300 5x300 5x300
#
# Second camera is activated with the "-r" option followed by the IP address and port
# of the second SkyX instance:
#
#       ./run_target-2 m51 5x300 5x300 5x300 5x300 -r 10.0.1.11:3040 3x240 3x240 3x240 3x240
#
# You can also add extra non-dithered frames to each set with an addition "x". For example:
#
#       ./run_target-2 m51 5x300x2 5x300 5x300 5x300
#
# will cause an LLRGB LLRGB pattern.
#
# Set the four variables below (altLimit = minumum starting altitude, guiderExposure =
# default guider exposure, guiderDelay = default guider delay, defaultFilter = the 
# filter you want to use for focusing and closed loop slews.
#
# If you want to use @F3 instead of @F2, just change the two "atFocus2" commands to
# "atFocus3" and substitute "NoRTZ" (with quotes) for target in the initial focus
# command to avoid it slewing back to target when it hasn't left. Leave target alone
# in the re-focus command in order to occasionally reset the dither and fix any other
# centering issues that may have occured.
#
# Ken Sturrock
# July 13, 2018
#

#############################
# User Modifiable Variables #
#############################

altLimit = 30
guiderExposure = "5"
guiderDelay = "0"
defaultFilter = "0"


####################
# Import Libraries #
####################

from library.PySkyX_ks import *

import time
import sys
import os
import datetime

########################
# Script set Variables #
########################

filterNumC1 = 0
filterNumC2 = 0
perFilC1 = []
perFilC2 = []
numExpC1 = []
numExpC2 = []
expDurC1 = []
expDurC2 = []
totalExpC1 = 0
totalExpC2 = 0
numDupC1 = []
numDupC2 = []
dupGoalC1 = 1
dupGoalC2 = 1
expCountC1 = 1
expCountC2 = 1
totalSecC1 = 0
totalSecC2 = 0
numSets = 0
numSets1 = 0
numSets2 = 0

####################
# Define Functions #
####################

def chkTarget():
#
# This validates the target and ensures that it is up & that it's night.
#
    timeStamp("Target is " + target + ".")

    if targExists(target) == "No":
        print("    ERROR: " + target + " not found in SkyX database.")
        softPark()
    
    isDayLight()

    currentHA = targHA(target)
    currentAlt = targAlt(target) 

    if currentAlt < altLimit and currentHA > 0:
        timeStamp("Target " + target + " is " + str(round(currentAlt, 2)) + " degrees high.")
        timeStamp("Target " + target + " has sunk too low.")
        softPark()
    
    while currentAlt < altLimit:
        print("     NOTE: Target " + target + " is " + str(round(currentAlt, 2)) + " degrees high.")
        print("     NOTE: Starting altitude is set for: " + str(altLimit) + " degrees.")
        print("     NOTE: Target " + target + " is still too low.")
        timeStamp("Waiting five minutes.")
        time.sleep (360)
        currentAlt = targAlt(target) 

def setupGuiding():
#
# This is a "macro" that calls several simpler functions in 
# order to setup autoguiding.
#
    camConnect("Guider")

    stopGuiding()

    time.sleep(5)

    takeImage("Guider", guiderExposure, "0", "NA")

    AGStar = findAGStar()

    if "Error" in AGStar:
        cloudWait()

        if CLSlew(target, defaultFilter) == "Fail":
            timeStamp("There was an error CLSing to Target. Stopping script.")
            hardPark()

        takeImage("Guider", guiderExposure, "0", "NA")

        AGStar = findAGStar()
     
        if "Error" in AGStar:
            print("    ERROR: Still cannot find a guide star. Sorry it didn't work out...")
            hardPark()
        else:
            XCoord,YCoord = AGStar.split(",")
    else:    
        XCoord,YCoord = AGStar.split(",")

    expRecommends = adjAGExposure(guiderExposure, guiderDelay, XCoord, YCoord)
    newGuiderExposure,newGuiderDelay = expRecommends.split(",")

    startGuiding(newGuiderExposure, newGuiderDelay, float(XCoord), float(YCoord))

def doAnImage(exposureTime, FilterNum):
#
# This function performs the general steps required to take 
# an image. By default, it doesn't mess with the delay and
# only manipulates the camera. It does a follow-up on the
# tracking.
#

    if TSXSend('ccdsoftCamera.PropStr("m_csObserver")') == "Ken Sturrock":
        if TSXSend("SelectedHardware.cameraModel") == "QSI Camera  ":
            TSXSend('ccdsoftCamera.setPropStr("m_csExCameraMode", "Higher Image Quality")')
            print("     NOTE: Setting QSI Camera to high quality mode.")

    if takeImage("Imager", exposureTime, "NA", FilterNum) == "Success":

        if TSXSend('ccdsoftCamera.PropStr("m_csObserver")') == "Ken Sturrock":
            if TSXSend("SelectedHardware.cameraModel") == "QSI Camera  ":
                TSXSend('ccdsoftCamera.setPropStr("m_csExCameraMode", "Faster Image Downloads")')
                print("     NOTE: Setting QSI Camera to faster download mode.")

        if isGuiderLost(setLimit) == "Yes":
            #
            # If the guider looks lost, try it again
            #
            time.sleep(5)
            if isGuiderLost(setLimit) == "Yes":
                print("    ERROR: Guider looks lost")
                return "Fail"


        else:
            print("     NOTE: Guider Tracking.")

            if getStats() == "Fail":
                print("    ERROR: Image Link Failed")
                return "Fail"

            return "Success"
    else:

        return "Fail"

        
######################
# Main Program Start #
######################

timeStamp("Script Running")

print("     DATE: " + datetime.date.today().strftime("%Y" + "-" + "%B" + "-" + "%d"))

print("     NOTE: SkyX Pro Build Level: " + TSXSend("Application.build"))

if sys.platform == "win32":
    print("     NOTE: Running on Windows.")

if sys.platform == "darwin":
    print("     NOTE: Running on Macintosh.")

if sys.platform == "linux":
	if os.uname()[4].startswith("arm"):
		print("     NOTE: Running on R-Pi.")
	else:
		print("     NOTE: Running on Linux.")

#
# preRun checks some settings to head off questions later
#
if preRun() == "Fail":
    sys.exit()

#####################################################################
# Take apart the arguments to figure out what the user wants to do. #
#####################################################################

totalArgs = (len(sys.argv) - 2)

if totalArgs < 1:
    timeStamp("ERROR. Not enough information.")
    print("           Syntax: " + sys.argv[0] + " target FxE FxE ...")
    sys.exit()


target = sys.argv[1]

camOneExp = []
camTwoExp = []
camTwoIP = "none"

counter = 1

while counter <= totalArgs:
    if sys.argv[counter + 1] == "-r":
        if (counter) < totalArgs:
            if "." in sys.argv[counter + 2]:
                camTwoIP = sys.argv[counter + 2]
                counter = counter + 2
            else:
                print("Invalid or incomplete IP address specified for second camera.")
                sys.exit()
        else:
            print("Insufficient arguments provided to specify second camera.")
            sys.exit()

        while counter <= totalArgs:
            camTwoExp.append(sys.argv[counter + 1])
            counter = counter + 1

    else:
        camOneExp.append(sys.argv[counter + 1])

    counter = counter + 1

totalFilC1 = len(camOneExp)
totalFilC2 = len(camTwoExp)

if totalFilC1 > totalFilC2:
    totalFil = totalFilC1
else:
    totalFil = totalFilC2

########################
# Is the target valid? #
########################

chkTarget()

print("     NOTE: Checking cameras.")
camConnect("Imager")

if camTwoIP != "none":
    camConnectRemote(camTwoIP, "Imager")


############################################
# Work out the imaging plan and explain it. #
############################################

print("     PLAN:")

print("           Local Camera")
print("           ------------")

while filterNumC1 < totalFilC1:
    
    perFilC1.append(camOneExp[filterNumC1])


    if perFilC1[filterNumC1].count("x") == 1:
        num,dur=perFilC1[filterNumC1].split("x")
        dup=1

    if perFilC1[filterNumC1].count("x") == 2:
        num,dur,dup=perFilC1[filterNumC1].split("x")

    numDupC1.append(int(dup))
    numExpC1.append(int(num))
    expDurC1.append(int(dur))

    if numDupC1[filterNumC1] == 1:
        adjExposureNum = numExpC1[filterNumC1]
    else:
        adjExposureNum = (numExpC1[filterNumC1] * numDupC1[filterNumC1])

    filName = TSXSend("ccdsoftCamera.szFilterName(" + str(filterNumC1) + ")")
     
    print ("           " + str(adjExposureNum) + " exposures for " + str(expDurC1[filterNumC1]) + " secs. with " + filName + " filter.")
    
    totalExpC1 = totalExpC1 + adjExposureNum
    totalSecC1 = totalSecC1 + (expDurC1[filterNumC1] * adjExposureNum)

    if numExpC1[filterNumC1] > numSets1:
        numSets1 = numExpC1[filterNumC1]
    
    filterNumC1 = filterNumC1 + 1
    
print("           -----")
print("           " + str(totalExpC1) + " total exposures for " + str(round((totalSecC1 / 60), 2)) + " total minutes.")
print("           -----")

if camTwoIP != "none":

    print(" ")
    print("           Remote Camera")
    print("           -------------")

    while filterNumC2 < totalFilC2:

        perFilC2.append(camTwoExp[filterNumC2])

        if perFilC2[filterNumC2].count("x") == 1:
            num,dur=perFilC2[filterNumC2].split("x")
            dup=1

        if perFilC2[filterNumC2].count("x") == 2:
            num,dur,dup=perFilC2[filterNumC2].split("x")
    
        numDupC2.append(int(dup))
        numExpC2.append(int(num))
        expDurC2.append(int(dur))
    
        if numDupC2[filterNumC2] == 1:
            adjExposureNum = numExpC2[filterNumC2]
        else:
            adjExposureNum = (numExpC2[filterNumC2] * numDupC2[filterNumC2])
    
        filName = TSXSend("ccdsoftCamera.szFilterName(" + str(filterNumC2) + ")")
         
        print ("           " + str(adjExposureNum) + " exposures for " + str(expDurC2[filterNumC2]) + " secs. with " + filName + " filter.")
        
        totalExpC2 = totalExpC2 + adjExposureNum
        totalSecC2 = totalSecC2 + (expDurC2[filterNumC2] * adjExposureNum)

        if numExpC2[filterNumC2] > numSets1:
            numSets1 = numExpC2[filterNumC2]
    
        filterNumC2 = filterNumC2 + 1
    
    print("           -----")
    print("           " + str(totalExpC2) + " total exposures for " + str(round((totalSecC2 / 60), 2)) + " total minutes.")
    print("           -----")
    print(" ")


if numSets1 >= numSets2:
    numSets = numSets1
else:
    numSets = numSets2

######################################
# Move the mount and start the setup #
######################################

#
# My Temmas need the help of Closed Loop Slew to make sure that they get on target
# and resynch. More modern mounts probably don't. If you want to use CLS then
# adjust the logic accordingly.
#
if "Temma" in TSXSend("SelectedHardware.mountModel"):
    if CLSlew(target, defaultFilter) == "Fail":
        timeStamp("There was an error on initial CLS. Stopping script.")
        softPark()
else:
    slew(target)

if camTwoIP != "none":
    slewRemote(camTwoIP, target)

if camTwoIP == "none":
    timeStamp("Conducting initial focus on local camera.")
    if atFocus2(target, defaultFilter) == "Fail":
        timeStamp("There was an error on initial focus. Stopping script.")
        softPark()
else:
    timeStamp("Conducting initial focus on both cameras.")
    if atFocus2Both(camTwoIP, target, defaultFilter) == "Fail":
        timeStamp("There was an error on initial focus. Stopping script.")
        softPark()


lastTargHA = targHA(target)
lastTemp = getTemp()
lastSeconds = round(time.monotonic(),0)

setLimit = calcSettleLimit()
setupGuiding()

#
# Figure out what to do if guider settling fails
#
if settleGuider(setLimit) == "Lost":
    print("    ERROR: Guiding setup failed.")
    stopGuiding()

    cloudWait()

    if CLSlew(target, defaultFilter) == "Fail":
        timeStamp("There was an error CLSing to Target. Stopping script.")
        hardPark()

    setupGuiding()

    setLimit = calcSettleLimit()

    if settleGuider(setLimit) == "Lost":
        print("    ERROR: Guiding setup failed again.")
        hardPark()

###############################
# Start the main imaging loop #
###############################

loopCounter = 1 

while loopCounter <= numSets:

    print("     -----")
    print("     NOTE: Starting image SET " + str(loopCounter) + " of " + str(numSets) + ".")
    
    fCounter = 0

    while fCounter < totalFil:

        dupCounter = 1
        dupGoalC1 = 1
        dupGoalC2 = 1
       
        if (fCounter <= len(numDupC1) - 1):
            dupGoalC1 = numDupC1[fCounter]

        if (fCounter <= len(numDupC2) - 1):
            dupGoalC2 = numDupC2[fCounter]

        while (dupCounter <= dupGoalC1) or (dupCounter <= dupGoalC2):

            if (fCounter <= (totalFilC2 - 1)) and (numExpC2[fCounter] > 0) and (dupCounter <= dupGoalC2):

                print("           -----")
                print("     NOTE: Starting remote camera image: " + str(expCountC2) + " of " + str(totalExpC2) + ".")
                
                takeImageRemote(camTwoIP, "Imager", str(expDurC2[fCounter]), "0", str(fCounter))
    
            if (fCounter <= (totalFilC1 - 1)) and (numExpC1[fCounter] > 0) and (dupCounter <= dupGoalC1):
                print("           -----")
                print("     NOTE: Starting local camera image " + str(expCountC1) + " of " + str(totalExpC1) + ".")
                expCountC1 = expCountC1 + 1
    
                if doAnImage(str(expDurC1[fCounter]), str(fCounter)) == "Fail":
                    print("    ERROR: Camera problem or clouds..")
    
                    stopGuiding()
    
                    cloudWait()
    
                    if CLSlew(target, defaultFilter) == "Fail":
                        timeStamp("There was an error CLSing to Target. Stopping script.")
                        hardPark()
    
                    setupGuiding()
    
                    setLimit = calcSettleLimit()
    
                    if settleGuider(setLimit) == "Lost":
                        print("    ERROR: Unable to setup guiding.")
                        hardPark()
                    else:
                        print("     NOTE: Attempting to retake image.")
                        if doAnImage(str(expDurC1[fCounter]), str(fCounter)) == "Fail":
                            print("    ERROR: There is still a problem.")
                            hardPark()
                        else:
                            print("     NOTE: Resuming Sequence.")
     
    
            if (fCounter <= (totalFilC2 - 1)) and (numExpC2[fCounter] > 0) and (dupCounter <= dupGoalC2):
                print("           -----")
                remoteImageDone(camTwoIP, "Imager")
                getStatsRemote(camTwoIP, "Imager")
                expCountC2 = expCountC2 + 1

            dupCounter = dupCounter + 1

        numExpC1[fCounter] = numExpC1[fCounter] - 1
        if (fCounter <= (totalFilC2 - 1)) and (numExpC2[fCounter] > 0):
            numExpC2[fCounter] = numExpC2[fCounter] - 1

        fCounter = fCounter + 1

    loopCounter = loopCounter + 1

    stopGuiding()
    print("     -----")
    print("     NOTE: Guiding Stopped.")
    print("     -----")

#########################################################
# Start the between-imaging-set housekeeping functions #
#########################################################

    if loopCounter <= numSets:
        isDayLight()

        if targAlt(target) < 35 and targHA(target) > 0:
            timeStamp("Target has sunk to low.")
            hardPark()

        currentTemp = getTemp()
        currentSeconds = round(time.monotonic(),0)

        if targHA(target) > 0 and lastTargHA <= 0:
            timeStamp("Target has crossed the meridian.")
                
            if "Temma" in TSXSend("SelectedHardware.mountModel"):
                if CLSlew(target, defaultFilter) == "Fail":
                    timeStamp("Error finding target post-flip. Stopping script.")
                    hardPark()
            else:
                slew(target)

            if camTwoIP == "none":
                atFocus2(target, defaultFilter)
            else:
                atFocus2Both(camTwoIP, target, defaultFilter)

            lastTemp = getTemp()
            lastSeconds = round(time.monotonic(),0)
            lastTargHA = targHA(target)

        elif abs(lastTemp - currentTemp) > 0.8 or (currentSeconds - lastSeconds) > 5400:
            print("     NOTE: Touching-up Focus.")
            if camTwoIP == "none":
                atFocus2(target, defaultFilter)
            else:
                atFocus2Both(camTwoIP, target, defaultFilter)
            
            lastTemp = getTemp()
            lastSeconds = round(time.monotonic(),0)
            dither()
        
        else:
            dither()

        #            
        # This checks to see if the mount has flipped by checking the "Beyond The Pole"
        # status. The idea is to warn the user that the script thinks the mount should 
        # be in one place but it's somewhere else, or vice versa. If you have a Paramount 
        # with a custom flip angle that is different from the meridian (a custom angle or 
        # the default angle on an MX) then this check might get triggered. In which case, 
        # either change the Paramount's flip angle to zero or change the compared HA 
        # value above from zero to match your mount's hour angle.
        #
        # I have also had reports of mounts flipping during a dither move, too, so this
        # will at least report that something odd may be happening.
        #
        # It's meaningless on the simulator.
        #
        if TSXSend("SelectedHardware.mountModel") !=  "Telescope Mount Simulator":
            TSXSend('sky6RASCOMTele.DoCommand(11, "")')
            if (TSXSend("sky6RASCOMTele.DoCommandOutput") == "1") and (targHA(target) > 0):
                print("    NOTE: The target is west of the meridian but the mount has not appeared to flip.")

            if (TSXSend("sky6RASCOMTele.DoCommandOutput") == "0") and (targHA(target) <= 0):
                print("    NOTE: The target is still east of the meridian but the mount appears to have flipped.")

        setupGuiding()

        if settleGuider(setLimit) == "Lost":
            print("    ERROR: Guiding setup failed.")
            stopGuiding()

            cloudWait()

            if CLSlew(target, defaultFilter) == "Fail":
                timeStamp("There was an error CLSing to Target. Stopping script.")
                hardPark()

            setupGuiding()

            setLimit = calcSettleLimit()

            if settleGuider(setLimit) == "Lost":
                print("    ERROR: Guiding setup failed again.")
                hardPark()

if camTwoIP != "none":
    print("     NOTE: Disconnecting remote camera.")
    camDisconnectRemote(camTwoIP, "Imager")

hardPark()

