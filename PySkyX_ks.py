#!/usr/bin/python3.4
import sys
print(sys.executable)
#
# Python library for automating SkyX
#
# Ken Sturrock
# August 05, 2018
#

TSXHost = "10.71.4.5"		# You can set this if you want to run the functions remotely
                                # The "*Remote functions" already handle that internally.
TSXPort = 3040                  # 3040 is the default, it can be changed

verbose = False			# Set this to "True" for debugging to see the Javascript traffic.

CR = "\n"			# A prettier shortcut for a newline.

import time
import socket
import os
import random
import math
import pathlib



def openDome():
    if TSXSend("sky6Dome.IsConnected")=="0":
        TSXSend("sky6Dome.Connect()")
        print("Connected Dome")
    print("Opening dome...")
    TSXSend("sky6Dome.OpenSlit()")
    print("Waiting... 30 s remaining")
    time.sleep(10)
    print("Waiting... 20 s remaining")
    time.sleep(10)
    print("Waiting... 10 s remaining")
    time.sleep(10)
    while TSXSend("sky6Dome.IsOpenComplete")=="0":
        pass
    
    if TSXSend("sky6Dome.slitState()")=="1" or TSXSend("sky6Dome.slitState()")=="3":
        print("Successfully opened dome")
    else:
        raise Exception("Dome open not successful!")

def closeDome():
    if TSXSend("sky6Dome.IsConnected")=="0":
        TSXSend("sky6Dome.Connect()")
        print("Connected Dome")
    print("Closing dome...")
    TSXSend("sky6Dome.CloseSlit()")
    print("Waiting... 30 s remaining")
    time.sleep(10)
    print("Waiting... 20 s remaining")
    time.sleep(10)
    print("Waiting... 10 s remaining")
    time.sleep(10)
    while TSXSend("sky6Dome.IsCloseComplete")=="0":
        pass
    
    if TSXSend("sky6Dome.slitState()")=="2" or TSXSend("sky6Dome.slitState()")=="4":
        print("Successfully closed dome")
    else:
        raise Exception("Dome close not successful!")

def domeDisconnect():
    if TSXSend("sky6Dome.IsConnected")=="1":
        print("Dome already disconnected")
    else:
        print("Disconnecting dome")
        TSXSend("sky6Dome.Disconnect()")
        if TSXSend("sky6Dome.IsConnected")=="1":
            print("Sucessfully disconnected dome")

def findDomeHome():
    if TSXSend("sky6Dome.IsConnected")=="0":
        TSXSend("sky6Dome.Connect()")
        print("Connected Dome")
    print("Finding home...")
    TSXSend("sky6Dome.FindHome()")
    print("Waiting... 100 s remaining")
    time.sleep(20)
    print("Waiting... 80 s remaining")
    time.sleep(20)
    print("Waiting... 60 s remaining")
    time.sleep(20)
    print("Waiting... 40 s remaining")
    time.sleep(20)
    print("Waiting... 20 s remaining")
    time.sleep(20)
    print("Dome successfully found home")


def connectMount():
    TSXSend("sky6RASCOMTele.Connect()")
    if TSXSend("sky6RASCOMTele.IsConnected")=="1":
        print("Successfully connected mount")
    else:
        raise Exception("Unsuccessful mount connection")

    TSXSend("sky6RASCOMTele.FindHome()")
    if TSXSend("sky6RASCOMTele.IsTracking")=="1":
        print("Mout found home, tracking at sidereal rate")

def parkAndDisconnectMount():
    TSXSend("sky6RASCOMTele.Park()")
    if TSXSend("sky6RASCOMTele.IsConnected")=="0":
        print("Successfully parked and disconnected mount")
    else:
        raise Exception("Unsuccessful park and disconnect")



def adjAGExposure(origAGExp, origAGDelay, XCoord, YCoord):
#
# Measure the brightness of the selected guide star and suggest tweaks
# if the star is really bright or really dim. Ideally, the star should
# not be saturated, because the star finder wouldn't have suggested it.
#
#

    if TSXSend("ccdsoftAutoguider.ImageReduction") != "0":

        print("     NOTE: Measuring AG exposure.")
    
        imageDepth = TSXSend('ccdsoftAutoguiderImage.FITSKeyword("BITPIX")')
        if "Error = 250" in imageDepth:
            print("     ERROR: FITS Keyword BITPIX not found. Assuming 16-bit.")
            imageDepth = 16

        newXCoord = float(TSXSend('ccdsoftAutoguider.BinX')) * float(XCoord)  
        newYCoord = float(TSXSend('ccdsoftAutoguider.BinY')) * float(YCoord)
    
        boxSizeVert = int(float(TSXSend("ccdsoftAutoguider.TrackBoxY")) / 2)
        boxSizeHoriz = int(float(TSXSend("ccdsoftAutoguider.TrackBoxX")) / 2)
    
        newTop = int(newYCoord - boxSizeVert)
        newBottom = int(newYCoord + boxSizeVert)
        newLeft = int(newXCoord - boxSizeHoriz)
        newRight = int(newXCoord + boxSizeHoriz)
    
        TSXSend("ccdsoftAutoguider.SubframeTop = " + str(newTop))
        TSXSend("ccdsoftAutoguider.SubframeLeft = " + str(newLeft))
        TSXSend("ccdsoftAutoguider.SubframeBottom = " + str(newBottom))
        TSXSend("ccdsoftAutoguider.SubframeRight = " + str(newRight))
    
        TSXSend("ccdsoftAutoguider.Subframe = true")
        TSXSend("ccdsoftAutoguider.Delay = 1")
        TSXSend("ccdsoftAutoguider.AutoSaveOn = false")
        TSXSend("ccdsoftAutoguider.ExposureTime = " + origAGExp)
    
        TSXSend("ccdsoftAutoguider.TakeImage()")
    
        fullWell = math.pow (2, int(imageDepth))
        brightestPix = TSXSend("ccdsoftAutoguider.MaximumPixel")
        brightness = round((int(brightestPix) / int(fullWell)), 2)
        print("     NOTE: AG Brightness: " + str(brightness))

        totalTime = float(origAGExp) + float(origAGDelay)


        if brightness >= 0.2 and brightness <= 0.8:
            print("     NOTE: No guider exposure change recommended.")
            return str(origAGExp) + "," + str(origAGDelay)

        else:
            units = brightness / float(origAGExp)
    
            if brightness > 0.8:
                print("     NOTE: Star too bright.")

                while brightness > 0.9:

                    origAGExp = float(origAGExp) / 2
                    TSXSend("ccdsoftAutoguider.ExposureTime = " + str(origAGExp))
                    TSXSend("ccdsoftAutoguider.TakeImage()")
                    fullWell = math.pow (2, int(imageDepth))
                    brightestPix = TSXSend("ccdsoftAutoguider.MaximumPixel")
                    brightness = round((int(brightestPix) / int(fullWell)), 2)
                    print("     NOTE: Exposure: " + str(origAGExp) + " Brightness: " + str(brightness))

                    units = brightness / float(origAGExp)

                newExp = 0.50 / units

            if brightness < 0.2:
                newExp = 0.3 / units
    
            newExp = round(newExp, 1)
            newDelay = float(totalTime) - float(newExp) 
            newDelay = round(newDelay, 1)
    
            if newDelay < 0:
                newDelay = 0
    
            if newExp > (float(origAGExp) * 1.5):
                newExp = (float(origAGExp) * 1.5)
    
            print("     NOTE: Recommend AG exposure of " + str(newExp) + " and a delay of " + str(newDelay) + ".")
            return str(newExp) + "," + str(newDelay)
    else:
        print("     NOTE: AG exposure not adjusted because guider is not calibrated.")
        return str(origAGExp) + "," + str(origAGDelay)


def atFocus2(target, filterNum):
#
# Focus using @F2. Because @Focus2 will sometimes do annoying stuff
# like choosing a focus star on the wrong side of the meridian, 
# we force the mount to jog east or west to get it away from the
# meridian if needed.
#
    if targHA(target) < 0.75 and targHA(target) > -0.75:
        print("     NOTE: Target is near the meridian.")
        if TSXSend("SelectedHardware.mountModel") !=  "Telescope Mount Simulator":
            TSXSend('sky6RASCOMTele.DoCommand(11, "")')
            if TSXSend("sky6RASCOMTele.DoCommandOutput") == "1":
                TSXSend('sky6RASCOMTele.Jog(420, "E")')
                print("     NOTE: OTA is west of the meridian pointing east.")
                print("     NOTE: Slewing towards the east, away from meridian.")
            else:
                TSXSend('sky6RASCOMTele.Jog(420, "W")')
                print("     NOTE: OTA is east of the meridian, pointing west.")
                print("     NOTE: Slewing towards the west, away from meridian.")
 
    if TSXSend("SelectedHardware.filterWheelModel") != "<No Filter Wheel Selected>":
        TSXSend("ccdsoftCamera.filterWheelConnect()")	
        TSXSend("ccdsoftCamera.FilterIndexZeroBased = " + filterNum) 

    if TSXSend("ccdsoftCamera.ImageUseDigitizedSkySurvey") == "1":
        timeStamp("@Focus2 success (simulated). Position = " + TSXSend("ccdsoftCamera.focPosition"))
        print("     NOTE: Returning to target.")
        if CLSlew(target, filterNum) == "Fail":
            hardPark()
        return "Success"

    else:  
        result = TSXSend("ccdsoftCamera.AtFocus2()")

        if "Process aborted." in result:
            timeStamp("Script Aborted.")
            sys.exit()

        if "Error" in result:
            timeStamp("@Focus2 failed: " + result)

            if CLSlew(target, filterNum) == "Fail":
                hardPark()

            return "Fail"
        else:

            TSXSend("sky6ObjectInformation.Property(0)")
            TSXSend("sky6ObjectInformation.ObjInfoPropOut")
            
            timeStamp("@Focus2 success.  Position = " + TSXSend("ccdsoftCamera.focPosition") + ". Star = " \
                    + TSXSend("sky6ObjectInformation.ObjInfoPropOut"))
            if CLSlew(target, filterNum) == "Fail":
                hardPark()
            return "Success"

def atFocus2Both(host, target, filterNum):
#
# Butchered version of @Focus2 routine to add a second camera.
#
# The only difference is that it calls the remote @Focus2 routine
# before slewing (both) back to target.
#
# It would probably be a lot easier to just use @Focus3 on the remote
# camera. If you use @Focus2, though, make sure that you calibrate
# the remote @Focus2 to use ther same magnitude stars as the main
# camera uses.
#


    if targHA(target) < 0.75 and targHA(target) > -0.75:
        print("     NOTE: Target is near the meridian.")
        if TSXSend("SelectedHardware.mountModel") !=  "Telescope Mount Simulator":
            TSXSend('sky6RASCOMTele.DoCommand(11, "")')
            if TSXSend("sky6RASCOMTele.DoCommandOutput") == "1":
                TSXSend('sky6RASCOMTele.Jog(420, "E")')
                print("     NOTE: OTA is west of the meridian pointing east.")
                print("     NOTE: Slewing towards the east, away from meridian.")
            else:
                TSXSend('sky6RASCOMTele.Jog(420, "W")')
                print("     NOTE: OTA is east of the meridian, pointing west.")
                print("     NOTE: Slewing towards the west, away from meridian.")
 
    if TSXSend("SelectedHardware.filterWheelModel") != "<No Filter Wheel Selected>":
        TSXSend("ccdsoftCamera.filterWheelConnect()")	
        TSXSend("ccdsoftCamera.FilterIndexZeroBased = " + filterNum) 

    if TSXSend("ccdsoftCamera.ImageUseDigitizedSkySurvey") == "1":
        timeStamp("@Focus2 success (simulated). Position = " + TSXSend("ccdsoftCamera.focPosition"))

        atFocusRemote(host, "Imager", "Two", filterNum )
        slewRemote(host, target)

        if CLSlew(target, filterNum) == "Fail":
            hardPark()
        return "Success"

    else:  
        result = TSXSend("ccdsoftCamera.AtFocus2()")

        if "Process aborted." in result:
            timeStamp("Script Aborted.")
            sys.exit()

        if "Error" in result:
            timeStamp("@Focus2 failed: " + result)

            if CLSlew(target, filterNum) == "Fail":
                hardPark()

            return "Fail"
        else:
            timeStamp("@Focus2 success.  Position = " + TSXSend("ccdsoftCamera.focPosition"))

            atFocusRemote(host, "Imager", "Two", filterNum )
            slewRemote(host, target)

            if CLSlew(target, filterNum) == "Fail":
                hardPark()
            return "Success"



def atFocus3(target, filterNum):
#
# This function runs @Focus3.
#
# Be aware that, if you're using this function, it's probably because you're
# trying to automate something. In which case, you're probably also dithering
# and you're also probably asleep. Even though @F3 doesn't require a slew back
# to target, this routine includes some code to periodically CLS back to
# your target both to reset the dither pattern and also because bad stuff
# happens and an occasional Return to Zero isn't bad. Until your mount comes
# back around. Specify target as "NoRTZ" to skip the recenter (for example, on 
# the initial focus).
#
# The @Focus3 JS command, itself, has two parameters. The "3" can be replaced by
# some other number to tell it how many samples to take & average at each position.
# Don't bother with two samples. Use one sample if your skies are great, five if 
# terrible and three for most places. The "true" tells it to select a subframe
# automatically. If you use "false" then you will have to define your own subframe
# or it will focus full-frame. It extracts the step size from the INI which you'll 
# have to set with the @F3 dialog box during a previous run.
#
    timeStamp("Focusing with @Focus3.")

    if TSXSend("SelectedHardware.filterWheelModel") != "<No Filter Wheel Selected>":
        TSXSend("ccdsoftCamera.filterWheelConnect()")	
        TSXSend("ccdsoftCamera.FilterIndexZeroBased = " + filterNum) 

    if TSXSend("ccdsoftCamera.ImageUseDigitizedSkySurvey") == "1":
        timeStamp("@Focus3 success (simulated). Position = " + TSXSend("ccdsoftCamera.focPosition"))
        if target != "NoRTZ":
            if random.choice('12') == "2":
                print("     NOTE: Recentering target.")
                if CLSlew(target, filterNum) == "Fail":
                    hardPark()
            else:
                print("     NOTE: Not recentering target at this time.")

        return "Success"

    else:  
        result = TSXSend("ccdsoftCamera.AtFocus3(3, true)")

        if "Process aborted." in result:
            timeStamp("Script Aborted.")
            sys.exit()

        if "Error" in result:
            timeStamp("@Focus3 failed: " + result)
            if target != "NoRTZ":
                if random.choice('12') == "2":
                    print("     NOTE: Recentering target.")
                    if CLSlew(target, filterNum) == "Fail":
                        hardPark()
                else:
                    print("     NOTE: Not recentering target at this time.")
            return "Fail"

        else:
            timeStamp("@Focus3 success. Position = " + TSXSend("ccdsoftCamera.focPosition"))
            if target != "NoRTZ":
                if random.choice('12') == "2":
                    print("     NOTE: Recentering target.")
                    if CLSlew(target, filterNum) == "Fail":
                        hardPark()
                else:
                    print("     NOTE: Not recentering target at this time.")

            return "Success"

def atFocusRemote(host, whichCam, method, filterNum):
#
# This is for focusing a second (or third) remote camera
#

    time.sleep(5)

    TSXSendRemote(host,"ccdsoftCamera.Asynchronous = false")

    if whichCam not in ("Imager", "Guider"):
        print("   ERROR: Please specify remote camera as either: Imager or Guider.")

    if whichCam == "Imager":
        if TSXSendRemote(host,"SelectedHardware.filterWheelModel") != "<No Filter Wheel Selected>":
            TSXSendRemote(host,"ccdsoftCamera.filterWheelConnect()")
            TSXSendRemote(host,"ccdsoftCamera.FilterIndexZeroBased = " + filterNum)

    if whichCam == "Guider":
        if TSXSendRemote(host,"SelectedHardware.autoguiderFilterWheelModel") != "<No Filter Wheel Selected>":
            TSXSendRemote(host,"ccdsoftAutoguider.filterWheelConnect()")
            TSXSendRemote(host,"ccdsoftAutoguider.FilterIndexZeroBased = " + filterNum)

    if whichCam == "Imager":    
        if method == "Three":
            timeStamp("Focusing remote imaging camera with @Focus3.")


            if (TSXSendRemote(host,"ccdsoftCamera.ImageUseDigitizedSkySurvey") == "1") or \
               (TSXSendRemote(host,"SelectedHardware.focuserModel") == "<No Focuser Selected>"):
                if TSXSendRemote(host,"ccdsoftCamera.ImageUseDigitizedSkySurvey") == "1":
                    timeStamp("@Focus3 success (simulated). Position = " + TSXSendRemote(host,"ccdsoftCamera.focPosition"))
                    return "Success"
                else:
                    timeStamp("No remote focuser detected.")
                    return "Success"

            else:  
                result = TSXSendRemote(host,"ccdsoftCamera.AtFocus3(3, true)")

                if "Process aborted." in result:
                    timeStamp("Script Aborted.")
                    sys.exit()

                if "Error" in result:
                    timeStamp("Remote @Focus3 failed: " + result)
                    return "Fail"

                else:
                    timeStamp("@Focus3 success. Position = " + TSXSendRemote(host,"ccdsoftCamera.focPosition"))
                    time.sleep(5)
                    return "Success"


        if method == "Two":
            timeStamp("Focusing remote imaging camera with @Focus2.")

            if (TSXSendRemote(host,"ccdsoftCamera.ImageUseDigitizedSkySurvey") == "1") or \
               (TSXSendRemote(host,"SelectedHardware.focuserModel") == "<No Focuser Selected>"):
                if TSXSendRemote(host,"ccdsoftCamera.ImageUseDigitizedSkySurvey") == "1":
                    timeStamp("@Focus2 success (simulated). Position = " + TSXSendRemote(host,"ccdsoftCamera.focPosition"))
                    return "Success"
                else:
                    timeStamp("No remote focuser detected.")
                    return "Success"


            else:  
                result = TSXSendRemote(host,"ccdsoftCamera.AtFocus2()")

                if "Process aborted." in result:
                    timeStamp("Script Aborted.")
                    sys.exit()

                if "Error" in result:
                    timeStamp("Remote @Focus2 failed: " + result)
                    return "Fail"

                else:
                    timeStamp("@Focus2 success. Position = " + TSXSendRemote(host,"ccdsoftCamera.focPosition"))
                    time.sleep(5)
                    return "Success"

    if whichCam == "Guider": 
        if method == "Three":
            timeStamp("Focusing remote guiding camera with @Focus3.")

            if (TSXSendRemote(host,"ccdsoftCamera.ImageUseDigitizedSkySurvey") == "1") or \
               (TSXSendRemote(host,"SelectedHardware.focuserModel") == "<No Focuser Selected>"):
                if TSXSendRemote(host,"ccdsoftCamera.ImageUseDigitizedSkySurvey") == "1":
                    timeStamp("@Focus3 success (simulated). Position = " + TSXSendRemote(host,"ccdsoftCamera.focPosition"))
                    return "Success"
                else:
                    timeStamp("No remote focuser detected.")
                    return "Success"

            else:  
                result = TSXSendRemote(host,"ccdsoftAutoguider.AtFocus3(3, true)")

                if "Process aborted." in result:
                    timeStamp("Script Aborted.")
                    sys.exit()

                if "Error" in result:
                    timeStamp("Remote @Focus3 failed: " + result)
                    return "Fail"

                else:
                    timeStamp("@Focus3 success. Position = " + TSXSendRemote(host,"ccdsoftAutoguider.focPosition"))
                    return "Success"


        if method == "Two":
            timeStamp("Focusing remote guiding camera with @Focus2.")

            if (TSXSendRemote(host,"ccdsoftCamera.ImageUseDigitizedSkySurvey") == "1") or \
               (TSXSendRemote(host,"SelectedHardware.focuserModel") == "<No Focuser Selected>"):
                if TSXSendRemote(host,"ccdsoftCamera.ImageUseDigitizedSkySurvey") == "1":
                    timeStamp("@Focus2 success (simulated). Position = " + TSXSendRemote(host,"ccdsoftCamera.focPosition"))
                    return "Success"
                else:
                    timeStamp("No remote focuser detected.")
                    return "Success"

            else:  
                result = TSXSendRemote(host,"ccdsoftAutoguider.AtFocus2()")

                if "Process aborted." in result:
                    timeStamp("Script Aborted.")
                    sys.exit()

                if "Error" in result:
                    timeStamp("Remote @Focus2 failed: " + result)
                    return "Fail"

                else:
                    timeStamp("@Focus2 success. Position = " + TSXSendRemote(host,"ccdsoftAutoguider.focPosition"))
                    return "Success"

    timeStamp("Remote focus completed.")



def calcImageScale(whichCam):
#
# Return the image scale for the supplied camera: Imager or Guider.
#

    if whichCam not in ("Imager", "Guider"):
        print("   ERROR: Please specify camera as either: Imager or Guider.")
        return "Fail"
    else:
     
        FITSProblem = "No"
        tempImage = "No"

        if whichCam == "Imager":
            camDevice = "ccdsoftCamera"
            camImage = "ccdsoftCameraImage"
            camAttachment = "AttachToActiveImager()"
        else:
            camDevice = "ccdsoftAutoguider"
            camImage = "ccdsoftAutoguiderImage"
            camAttachment = "AttachToActiveAutoguider()"
    
        if "206" in str(TSXSend(camImage + "." + camAttachment)):
            print("     NOTE: No current image available.")
            tempImage = "Yes"
            if "Error" in takeImage (whichCam, "1", "0", "0"):
                softPark()

            TSXSend(camImage + "." + camAttachment)
    
        if TSXSend(camDevice + ".ImageUseDigitizedSkySurvey") == "1":
            FITSProblem = "Yes"
        
        else:
            if "250" in str(TSXSend(camImage + '.FITSKeyword("FOCALLEN")')):
                print("     NOTE: FOCALLEN keyword not found in FITS header.")
                FITSProblem = "Yes"
    
            if "250" in str(TSXSend(camImage + '.FITSKeyword("XPIXSZ")')):
                print("     NOTE: XPIXSZ keyword not found in FITS header.")
                FITSProblem = "Yes"
    
        if FITSProblem == "Yes":
            ImageScale = 1.70
    
        else: 
            FocalLength = TSXSend(camImage + '.FITSKeyword("FOCALLEN")')
            PixelSize =  TSXSend(camImage + '.FITSKeyword("XPIXSZ")')
            Binning =  TSXSend(camImage + '.FITSKeyword("XBINNING")')

            # 
            # This "real" stuff is needed because T-Point loves to automagically
            # switch your automated ImageLink settings to 2x2 binning which requires
            # us to devide the reported pixel size by the binning and then rescale
            # according to the selected imaging binning for the camera
            #
            realPixelSize = (float(PixelSize) / float(Binning))
            realBinning = TSXSend(camDevice + '.BinX')

            ImageScale = ((float(realPixelSize) * float(realBinning)) / float(FocalLength) ) * 206.3
            ImageScale = round(float(ImageScale), 2)

        if tempImage == "Yes":
            Path = TSXSend(camImage + ".Path")
            if os.path.exists(Path):
                os.remove(Path)

        print("     NOTE: " + whichCam + " image scale is " + str(ImageScale) + " AS/Pixel.")
        return ImageScale

def calcSettleLimit():
#
# Calculate a reasonable settle threshold based on image scale
#
    timeStamp("Determining guider settle limit.")

    AGImageScale = calcImageScale("Guider")
    ImageScale = calcImageScale("Imager")

    pixelRatio = ImageScale / AGImageScale
    pixelRatio = round(pixelRatio, 2)
    print("     NOTE: Image scale ratio set to: " + str(pixelRatio) + ".")

    settleThreshold = round((pixelRatio * 0.95), 2)

    #
    # This was done because my Takahashi mounts track like drunk sailors.
    #
    if TSXSend('ccdsoftCamera.PropStr("m_csObserver")') == "Ken Sturrock":
        if "Temma" in TSXSend("SelectedHardware.mountModel"):
            settleThreshold = 3
            print("     NOTE: Settle range enlarged for Ken's Temmas")

    #
    # I have no confidence that less than 1/5 of a pixel is a realistic expectation.
    # Remember that the settle threshold doesn't affect the guider's performance,
    # it just sets how long the script waits before moving on.
    #
    if settleThreshold < 0.2:
        settleThreshold = 0.2

    print("     NOTE: Calculated settle limit: " + str(settleThreshold) + " guider pixels.")

    return settleThreshold


def camConnect(whichCam):
#
# This function connects the specified camera
#
    if whichCam == "Guider":
        out = TSXSend("ccdsoftAutoguider.Connect()")

    elif whichCam == "Imager":
        TSXSend("ccdsoftCamera.Disconnect()")

        if str(TSXSend('ccdsoftCamera.PropStr("m_csObserver")')) ==  "Ken Sturrock":
            print("     NOTE: Setting imaging camera to -10.")
            TSXSend("ccdsoftCamera.TemperatureSetPoint = -10")
            TSXSend("ccdsoftCamera.RegulateTemperature = true")
            time.sleep(1)

        out = TSXSend("ccdsoftCamera.Connect()")
    else:
        out = "Unknown Camera: " + whichCam

    if out != "0":
        timeStamp("Unable to connect: " + whichCam)
        return "Fail"
    else:
        print("Successfully connected camera")
        return "Success"

def camDisconnect(whichCam):
#
# This function disconnects the specified camera
#
    if whichCam == "Guider":
        out = TSXSend("ccdsoftAutoguider.Disconnect()")
    elif whichCam == "Imager":
        out = TSXSend("ccdsoftCamera.Disconnect()")
    else:
        out = "Unknown Camera: " + whichCam

    if out != "0":
        timeStamp("Unable to disconnect: " + whichCam)
        return "Fail"
    else:
        print("Successfully disconnected camera")
        return "Success"

def camConnectRemote(host, whichCam):
#
# This function connects the specified camera
#
    if whichCam == "Guider":
        out = TSXSendRemote(host,"ccdsoftAutoguider.Connect()")

    elif whichCam == "Imager":
        TSXSendRemote(host,"ccdsoftCamera.Disconnect()")
        if str(TSXSend('ccdsoftCamera.PropStr("m_csObserver")')) ==  "Ken Sturrock":
            TSXSendRemote(host, "ccdsoftCamera.TemperatureSetPoint = -10")
            TSXSendRemote(host, "ccdsoftCamera.RegulateTemperature = true")
            time.sleep(1)
        
        out = TSXSendRemote(host,"ccdsoftCamera.Connect()")
    else:
        out = "Unknown Camera: " + whichCam

    if out != "0":
        timeStamp("Unable to connect: " + whichCam)
        return "Fail"
    else:
        return "Success"

def camDisconnectRemote(host, whichCam):
#
# This function disconnects the specified camera
#
    if whichCam == "Guider":
        out = TSXSendRemote(host,"ccdsoftAutoguider.Disconnect()")
    elif whichCam == "Imager":
        out = TSXSendRemote(host,"ccdsoftCamera.Disconnect()")
    else:
        out = "Unknown Camera: " + whichCam

    if out != "0":
        timeStamp("Unable to disconnect: " + whichCam)
        return "Fail"
    else:
        return "Success"


def cloudWait():
#
# Switch off the sidereal drive and wait five minutes.
# Then, keep checking for stars every five minutes for
# the next 25 minutes.
#
    shouldWait = "Yes"
    counter = 1

    timeStamp("Waiting five minutes. (1 of 5)")
    if TSXSend("SelectedHardware.mountModel") !=  "Telescope Mount Simulator":
        TSXSend("sky6RASCOMTele.SetTracking(0, 1, 0 ,0)")

    camDisconnect("Guider")
    camDisconnect("Imager")

    time.sleep(300)

    counter = counter + 1

    while shouldWait == "Yes" and counter <= 5:

        if str(TSXSend("SelectedHardware.mountModel") !=  "Telescope Mount Simulator"):
            TSXSend("sky6RASCOMTele.SetTracking(1, 1, 0 ,0)")
            time.sleep(10)

        timeStamp("Testing sky for clouds.")
        camConnect("Guider")
        takeImage("Guider", "5", "0", "NA")
        AGStar = findAGStar()

        if not "Error" in AGStar:
            shouldWait = "No"
            timeStamp("Sky appears clear.")
        else:
            timeStamp("Sky still appears cloudy.")

            camDisconnect("Guider")
            if TSXSend("SelectedHardware.mountModel") !=  "Telescope Mount Simulator":
                TSXSend("sky6RASCOMTele.SetTracking(0, 1, 0 ,0)")

            print("     NOTE: Waiting five minutes. (" + str(counter) + " of 5)")

            time.sleep(300)

            if shouldWait == "Yes":
                print("     NOTE: Attempting to continue.")
            
    camConnect("Guider")
    camConnect("Imager")

    if str(TSXSend("SelectedHardware.mountModel") !=  "Telescope Mount Simulator"):
        TSXSend("sky6RASCOMTele.SetTracking(1, 1, 0 ,0)")

    time.sleep(10)

def CLSlew(target, filterNum):
#
# This uses Closed Loop Slew to precisely center the target.
#
# There is a hack, however, because it uses regular slew to "pre-slew" to the
# target before evoking Closed Loop Slew. This is done because I own a slow
# mount which might time out with a regular CLS. In practice, it adds no real
# time penalty, so I do it for all mounts. The 10 second delay is also a
# Temma mitigation stratedgy to make sure that the mount really has stopped
# moving before the image is taken.
#
# Finally, you guessed it, the resynch is important for a poor-pointing mount 
# like my Takahashi. 
# 
    slew(target)

    timeStamp("Attempting precise positioning with CLS.")


    if TSXSend("SelectedHardware.filterWheelModel") != "<No Filter Wheel Selected>":
        TSXSend("ccdsoftCamera.filterWheelConnect()")	
        TSXSend("ccdsoftCamera.FilterIndexZeroBased = " + filterNum) 

    if TSXSend("ccdsoftCamera.ImageUseDigitizedSkySurvey") == "1":
        timeStamp("CLS to " + target + " success (simulated).")
        
        return "Success"
    else:    
        camDelay = TSXSend("ccdsoftCamera.Delay")

        TSXSend("ccdsoftCamera.Delay = 10")

        CLSResults = TSXSend("ClosedLoopSlew.exec()")

        if "failed" in CLSResults:
            if "651" in CLSResults:
                CLSResults = "Not Enough Stars in the Photo. Error = 651"

            print("    ERROR: " + CLSResults)
            timeStamp("CLS to " + target + " failed.")

            TSXSend("ccdsoftCamera.Delay = " + camDelay)

            return "Fail"

        else:
            TSXSend('sky6StarChart.Find("Z 90")')
            TSXSend('sky6StarChart.Find("' + target + '")')
    
            iScale = TSXSend("ImageLinkResults.imageScale")
            timeStamp("CLS to " + target + " success (" + iScale + " AS/pixel).")
        
            TSXSend("ccdsoftCamera.Delay = " + camDelay)

            if "Temma" in TSXSend("SelectedHardware.mountModel"):
                reSynch()

            return "Success"

def dither():
#
# This function dithers the mount based on image scale and declination
#
# It does not "guide to the destination". You must stop guiding and then 
# restart it after.
#

    timeStamp("Calculating dither distance.")
    imageScale = calcImageScale("Imager")

    if imageScale != "Fail":
        maxMove = (imageScale * 6) 
        ditherXsec = maxMove * random.uniform(0.1,1)
        ditherYsec = maxMove * random.uniform(0.1,1)

        TSXSend("sky6ObjectInformation.Property(55)") 	
        targDec = TSXSend("sky6ObjectInformation.ObjInfoPropOut")
        targRads = abs(float(targDec)) * (3.14159/ 180)
        radsValue = math.cos(targRads)
        decFactor = (1 / radsValue)
        if decFactor > 10:
            decFactor = 10

        ditherYsec = ditherYsec * decFactor

        ditherXMin = ditherXsec * 0.01666666666
        ditherYMin = ditherYsec * 0.01666666666

        NorS = random.choice([True, False])
        if NorS == True:
            NorS = "N"
        else:
            NorS = "S"

        EorW = random.choice([True, False])
        if EorW == True:
            EorW = "E"
        else:
            EorW = "W"

        TSXSend('sky6RASCOMTele.Jog(' + str(ditherXMin) + ', "' + str(NorS) + '")')

        time.sleep(1)

        TSXSend('sky6RASCOMTele.Jog(' + str(ditherYMin) + ', "' + str(EorW) + '")')

        time.sleep(1)

        timeStamp("Dithered: " + str(round(ditherXsec, 1)) + " AS (" + str(NorS) + "), " + str(round(ditherYsec, 1)) + " AS (" + str(EorW) + ")")

        time.sleep(5)

        if TSXSend('ccdsoftCamera.PropStr("m_csObserver")') == "Ken Sturrock":
            if "Temma" in TSXSend("SelectedHardware.mountModel"):
                print("     NOTE: Pausing 30 seconds to take-up backlash for Ken's Temmas.")
                time.sleep(30)


def findAGStar():
#
# This incredible mess is a straight copy of JS code into a "here document".
#
# If you want to grok what it's doing, check out the "diagnostic" version in
# the original bash/JS script set JS_Codons directory.
#
# This code includes ideas (and code) from Ken Sturrock, Colin McGill and 
# Kym Haines. Although it's probably not recognizable by any of us.
#
# Someday, I may re-write it into Python, but maybe not. Just cover your eyes
# and trust the force.
#

    AGFindResults = TSXSend('''

var CAGI = ccdsoftAutoguiderImage; CAGI.AttachToActiveAutoguider();
CAGI.ShowInventory(); var X = CAGI.InventoryArray(0), Y =
CAGI.InventoryArray(1), Mag = CAGI.InventoryArray(2), FWHM =
CAGI.InventoryArray(4), Elong = CAGI.InventoryArray(8); var disMag =
CAGI.InventoryArray(2), disFWHM = CAGI.InventoryArray(4), disElong =
CAGI.InventoryArray(8); var Width = CAGI.WidthInPixels, Height =
CAGI.HeightInPixels; function median(values) { values.sort( function(a,b)
{return a - b;} ); var half = Math.floor(values.length/2); if(values.length
% 2) { return values[half]; } else { return (values[half-1] + values[half])
/ 2.0; } } function QMagTest(ls) { var Ix = 0, Iy = 0, Isat = 0, Msat =
0.0; for (Ix = Math.max(0,Math.floor(X[ls]-FWHM[ls]*2+.5)); Ix <
Math.min(Width-1,X[ls]+FWHM[ls]*2); Ix++ ) { for (Iy =
Math.max(0,Math.floor(Y[ls]-FWHM[ls]*2+.5)); Iy <
Math.min(Height-1,Y[ls]+FWHM[ls]*2); Iy++ ) { if (ImgVal[Iy][Ix] > Msat)
Msat = ImgVal[Iy][Ix]; if (ImgVal[Iy][Ix] > GuideMax) Isat++; } } if (Isat
> 1) { ADUFail = ADUFail + 1; return false; } else { return true; } } var
FlipY = "No", out = "", Brightest = 0, newX = 0, newY = 0,
counter = X.length, failCount = 0, magLimit = 0, k = 0; var passedLS = 0,
ADUFail = 0, medFWHM = median(disFWHM), medMag = median(disMag), medElong =
median(disElong), baseMag = medMag; var halfTBX =
(ccdsoftAutoguider.TrackBoxX / 2) + 5, halfTBY =
(ccdsoftAutoguider.TrackBoxY / 2) + 5, distX = 0, distY = 0, pixDist = 0;
var ImgVal = new Array(Height), Ix = 0, Iy = 0, GuideBits =
CAGI.FITSKeyword("BITPIX"), GuideCamMax = Math.pow(2,GuideBits)-1, GuideMax
= GuideCamMax * 0.9; for (Ix = 0; Ix < Height; Ix++) { ImgVal[Ix] =
CAGI.scanLine(Ix); } var NcoarseX   = Math.floor(Width/halfTBX+1); var
NcoarseY   = Math.floor(Height/halfTBY+1); var CoarseArray = new
Array(NcoarseX); for (Ix = 0; Ix < NcoarseX; Ix++) { CoarseArray[Ix] = new
Array(NcoarseY); for (Iy = 0; Iy < NcoarseY; Iy++) CoarseArray[Ix][Iy] =
new Array(); } for (ls = 0; ls < counter; ls++) { Ix =
Math.floor(X[ls]/halfTBX); Iy = Math.floor(Y[ls]/halfTBY);
CoarseArray[Ix][Iy].push(ls); } function QNeighbourTest(ls) { var Ix, Iy,
Is, MagLimit = (Mag[ls] + medMag) / 2.5, distX, distY, pixDist, Nstar,
Istar; var Isx = Math.floor(X[ls]/halfTBX); var Isy =
Math.floor(Y[ls]/halfTBY); var Ixmin = Math.max(0,Isx-1); var Ixmax =
Math.min(NcoarseX-1,Isx+1); var Iymin = Math.max(0,Isy-1); var Iymax =
Math.min(NcoarseY-1,Isy+1); for (Ix = Ixmin; Ix < Ixmax; Ix++) { for (Iy =
Iymin; Iy < Iymax; Iy++) { Nstar = CoarseArray[Ix][Iy].length; for (Is = 0;
Is < Nstar; Is++) { Istar = CoarseArray[Ix][Iy][Is]; if (Istar != ls) {
distX = Math.abs(X[ls] - X[Istar]); distX = distX.toFixed(2); distY =
Math.abs(Y[ls] - Y[Istar]); distY = distY.toFixed(2); pixDist =
Math.sqrt((distX * distX) + (distY * distY)); pixDist = pixDist.toFixed(2);
if (  distX > halfTBX ||  distY > halfTBY || Mag[k] > MagLimit) { } else {
return (false); } } } } } return (true); } for (ls = 0; ls < counter; ++ls)
{ if ( Mag[ls] < medMag ) { if (((X[ls] > halfTBX && X[ls] < (Width -
halfTBX))) && (Y[ls] > halfTBY && Y[ls] < (Height - halfTBY))) { if
((Elong[ls] < medElong * 2.5)) { if (FWHM[ls] < (medFWHM * 2.5) &&
(FWHM[ls] > 1)) { if ( QMagTest(ls) ) { if ( QNeighbourTest(ls)) { passedLS
= passedLS + 1; if (Mag[ls] < baseMag) { baseMag = Mag[ls]; Brightest = ls;
} } } } } } } } if ( ccdsoftAutoguider.ImageUseDigitizedSkySurvey == "1" )
{ FlipY = "Yes"; var Binned = CAGI.FITSKeyword ("XBINNING"); if ( Binned >
1 ) { FlipY = "No"; } } if (FlipY == "Yes") { newY = (Height -
Y[Brightest]); } else { newY = Y[Brightest]; } newY = newY.toFixed(2); newX
= X[Brightest].toFixed(2); out = newX + "," + newY + "," + CAGI.Path
	''')

    if "TypeError" in AGFindResults:
        timeStamp("Error analyzing guider image for a suitable guide star.")
        return "Error,Error"
    else:
        XCoord,YCoord,Path=AGFindResults.split(",")
        timeStamp("Found a nice guide star at: " + XCoord + ", " + YCoord)
        Path = Path.split(".")[0]

        if os.path.exists(Path + ".fit"):
            os.remove(Path + ".fit")
 
        if os.path.exists(Path + ".SRC"):
            os.remove(Path + ".SRC")
 
        return XCoord + "," + YCoord


def getActiveImagePath():
#
# Quick procedure to assign the active camera image to ccdsoftCamera (not guider)
# and return the OS-specific path.
#

    TSXSend("ccdsoftCameraImage.AttachToActiveImager()")
    imgPath=TSXSend("ccdsoftCameraImage.Path")

    return imgPath
 
def getStats():
#
# Pull some basic statistics for display from the imaging camera. 
# Uses Image Link, so it's kind of slow - especially on a RPi.
#

    if TSXSend("ccdsoftCamera.ImageUseDigitizedSkySurvey") != "1":

        print("    STATS:")

        TSXSend("ccdsoftCameraImage.AttachToActiveImager()")

        TSXSend("ImageLink.pathToFITS = ccdsoftCameraImage.Path")
        if "TypeError: " not in TSXSend("ImageLink.execute()"):

            imageScale = TSXSend("ImageLinkResults.imageScale")
            avgPixelValue = TSXSend("ccdsoftCameraImage.averagePixelValue()")
            imageCenterRA = TSXSend("ImageLinkResults.imageCenterRAJ2000")
            imageCenterDec = TSXSend("ImageLinkResults.imageCenterDecJ2000")
            positionAngle = TSXSend("ImageLinkResults.imagePositionAngle")
            ilFWHM = TSXSend("ImageLinkResults.imageFWHMInArcSeconds")
            ASIlFWHM = float(ilFWHM) * float(imageScale)
            TSXSend("sky6Utils.ConvertEquatorialToString(" + imageCenterRA + ", " + imageCenterDec + ", 5)")
            centerHMS2k = TSXSend("sky6Utils.strOut")
            TSXSend("sky6Utils.Precess2000ToNow(" + imageCenterRA + ", " + imageCenterDec + ")")
            centerLSRANow = TSXSend("sky6Utils.dOut0")
            centerLSDecNow = TSXSend("sky6Utils.dOut1")
            TSXSend("sky6Utils.ConvertEquatorialToString(" + centerLSRANow + ", " + centerLSDecNow + ", 5)")	
            centerHMSNow = TSXSend("sky6Utils.strOut")

            dirName,fileName = os.path.split(TSXSend("ccdsoftCameraImage.Path"))
            
            orgImgName = fileName.split(".")[0]

            if os.path.exists(dirName + "/" + orgImgName + ".SRC"):
                os.remove(dirName + "/" + orgImgName + ".SRC")
     
            if os.path.exists(dirName + "/Cropped " + orgImgName + ".fit"):
                os.remove(dirName + "/Cropped " + orgImgName + ".fit")

            if os.path.exists(dirName + "/Cropped " + orgImgName + ".SRC"):
                os.remove(dirName + "/Cropped " + orgImgName + ".SRC")


            filterKeyword = TSXSend('ccdsoftCameraImage.FITSKeyword("FILTER")')
            if not "Error = 250" or "Undefined" in filterKeyword:
                print("           Filter:               " + filterKeyword)

            print("           Image Scale:          " + str(imageScale) + " AS/Pixel")
            print("           Image FWHM:           " + str(round(ASIlFWHM, 2)) + " AS")
            print("           Average Pixel Value:  " + avgPixelValue.split(".")[0] + " ADU")
            print("           Position Angle:       " + positionAngle.split(".")[0] + " degrees")
            print("           Focuser Position:     " + TSXSend("ccdsoftCamera.focPosition"))
            print("           Temperature:          " + TSXSend("ccdsoftCamera.focTemperature.toFixed(1)")) 
            
            altKeyword = TSXSend('ccdsoftCameraImage.FITSKeyword("CENTALT")')
            if not "Error = 250" or "Undefined" in altKeyword:
                altKeyword = round(float(altKeyword), 2)
                print("           Image Altitude:       " + str(altKeyword))

            azKeyword = TSXSend('ccdsoftCameraImage.FITSKeyword("CENTAZ")')
            if not "Error = 250" or "Undefined" in azKeyword:
                azKeyword = round(float(azKeyword), 2)
                print("           Image Aziumth:        " + str(azKeyword))

            print("           Image Center (J2k):   " + centerHMS2k)
            print("           Image Center (JNow):  " + centerHMSNow)
            
            return "Success"

        else:
            print("    ERROR: Image Link failed.")
            
            return "Fail" 
    else:
        print("     NOTE: DSS images are in use. Skipping statistics.")
        
        return "Success"



def getStatsPath(imgPath):
#
# Pull some basic statistics for display from a path. 
# Uses Image Link, so it's kind of slow - especially on a RPi.
#

    new_dir_name = pathlib.Path(imgPath)

    if sys.platform == "win32":
        #
        # Because the path uses back-slashes, we must protect them with an additional
        # back-slash so that Javascript on SkyX doesn't interperate them as special
        # character codes when we feed them over the IP port.
        #
        print("     NOTE: MS-DOS style path.")
        print("     NOTE: Directory is " + str(new_dir_name.parent))
        print("     NOTE: File is " + new_dir_name.name)
        new_dir_name = str(new_dir_name).replace("\\", "\\\\")
    else:
        print("     NOTE: MS-DOS style path.")
        print("     NOTE: Directory is " + str(new_dir_name.parent))
        print("     NOTE: File is " + new_dir_name.name)
        new_dir_name = str(new_dir_name).replace("\\", "\\\\")

    print("     NOTE: Attempting Image Link:")

    TSXSend('ImageLink.pathToFITS = "' + new_dir_name + '"')

    if "TypeError: " not in TSXSend("ImageLink.execute()"):

        imageScale = TSXSend("ImageLinkResults.imageScale")
        imageCenterRA = TSXSend("ImageLinkResults.imageCenterRAJ2000")
        imageCenterDec = TSXSend("ImageLinkResults.imageCenterDecJ2000")
        positionAngle = TSXSend("ImageLinkResults.imagePositionAngle")
        ilFWHM = TSXSend("ImageLinkResults.imageFWHMInArcSeconds")
        ASIlFWHM = float(ilFWHM) * float(imageScale)
        TSXSend("sky6Utils.ConvertEquatorialToString(" + imageCenterRA + ", " + imageCenterDec + ", 5)")
        centerHMS2k = TSXSend("sky6Utils.strOut")
        TSXSend("sky6Utils.Precess2000ToNow(" + imageCenterRA + ", " + imageCenterDec + ")")
        centerLSRANow = TSXSend("sky6Utils.dOut0")
        centerLSDecNow = TSXSend("sky6Utils.dOut1")
        TSXSend("sky6Utils.ConvertEquatorialToString(" + centerLSRANow + ", " + centerLSDecNow + ", 5)")	
        centerHMSNow = TSXSend("sky6Utils.strOut")

        filterKeyword = TSXSend('ccdsoftCameraImage.FITSKeyword("FILTER")')

        if not "Error = 250" or "Undefined" in filterKeyword:
            print("           Filter:               " + filterKeyword)

        print("           Image Scale:          " + str(imageScale) + " AS/Pixel")
        print("           Image FWHM:           " + str(round(ASIlFWHM, 2)) + " AS")
        print("           Position Angle:       " + positionAngle.split(".")[0] + " degrees")
            
        altKeyword = TSXSend('ccdsoftCameraImage.FITSKeyword("CENTALT")')

        if not "Error = 250" or "Undefined" in altKeyword:
            altKeyword = round(float(altKeyword), 2)
            print("           Image Altitude:       " + str(altKeyword))

        azKeyword = TSXSend('ccdsoftCameraImage.FITSKeyword("CENTAZ")')
        if not "Error = 250" or "Undefined" in azKeyword:
            azKeyword = round(float(azKeyword), 2)
            print("           Image Aziumth:        " + str(azKeyword))

        print("           Image Center (J2k):   " + centerHMS2k)
        print("           Image Center (JNow):  " + centerHMSNow)
            
        return "Success"

    else:
        print("    ERROR: Image Link failed.")
        return "Fail" 

def getStatsRemote(host, whichCam):
#
# Pull some basic statistics for display from the remote computer's imaging (not guiding) camera.
# Uses Image Link, so it's kind of slow - especially on a RPi.
#
# Because we are only controlling the remote machine via SkyX,
# we can't clean up the SRC scratch files.
#
    if whichCam not in ("Imager", "Guider"):
        print("   ERROR: Please specify remote camera as either: Imager or Guider.")

    if whichCam == "Imager":

        if TSXSendRemote(host,"ccdsoftCamera.ImageUseDigitizedSkySurvey") != "1":
    
            print("    STATS:")
    
            TSXSendRemote(host,"ccdsoftCameraImage.AttachToActiveImager()")
    
            TSXSendRemote(host,"ImageLink.pathToFITS = ccdsoftCameraImage.Path")
            if "TypeError: " not in TSXSendRemote(host,"ImageLink.execute()"):
    
                imageScale = TSXSendRemote(host,"ImageLinkResults.imageScale")
                avgPixelValue = TSXSendRemote(host,"ccdsoftCameraImage.averagePixelValue()")
                imageCenterRA = TSXSendRemote(host,"ImageLinkResults.imageCenterRAJ2000")
                imageCenterDec = TSXSendRemote(host,"ImageLinkResults.imageCenterDecJ2000")
                positionAngle = TSXSendRemote(host,"ImageLinkResults.imagePositionAngle")
                ilFWHM = TSXSendRemote(host,"ImageLinkResults.imageFWHMInArcSeconds")
                ASIlFWHM = float(ilFWHM) * float(imageScale)
                TSXSendRemote(host,"sky6Utils.ConvertEquatorialToString(" + imageCenterRA + ", " + imageCenterDec + ", 5)")
                centerHMS2k = TSXSendRemote(host,"sky6Utils.strOut")
                TSXSendRemote(host,"sky6Utils.Precess2000ToNow(" + imageCenterRA + ", " + imageCenterDec + ")")
                centerLSRANow = TSXSendRemote(host,"sky6Utils.dOut0")
                centerLSDecNow = TSXSendRemote(host,"sky6Utils.dOut1")
                TSXSendRemote(host,"sky6Utils.ConvertEquatorialToString(" + centerLSRANow + ", " + centerLSDecNow + ", 5)")	
                centerHMSNow = TSXSendRemote(host,"sky6Utils.strOut")

                filterKeyword = TSXSendRemote(host,'ccdsoftCameraImage.FITSKeyword("FILTER")')
                if not "Error = 250" or "Undefined" in filterKeyword:
                    print("           Filter:               " + filterKeyword)

                print("           Image Scale:          " + str(imageScale) + " AS/Pixel")
                print("           Image FWHM:           " + str(round(ASIlFWHM, 2)) + " AS")
                print("           Average Pixel Value:  " + avgPixelValue.split(".")[0] + " ADU")
                print("           Position Angle:       " + positionAngle.split(".")[0] + " degrees")
                print("           Focuser Position:     " + TSXSendRemote(host,"ccdsoftCamera.focPosition"))
                print("           Temperature:          " + TSXSendRemote(host,"ccdsoftCamera.focTemperature.toFixed(1)")) 
                
                altKeyword = TSXSendRemote(host,'ccdsoftCameraImage.FITSKeyword("CENTALT")')
                if not "TypeError" or "Undefined" in altKeyword:
                    altKeyword = round(float(altKeyword), 2)
                    print("           Image Altitude:       " + str(altKeyword))
    
    
                azKeyword = TSXSendRemote(host,'ccdsoftCameraImage.FITSKeyword("CENTAZ")')
                if not "TypeError" or "Undefined" in azKeyword:
                    azKeyword = round(float(azKeyword), 2)
                    print("           Image Aziumth:        " + str(azKeyword))
    
                print("           Image Center (J2k):   " + centerHMS2k)
                print("           Image Center (JNow):  " + centerHMSNow)
    
                print("     NOTE: Unable to cleanup light source (SRC) scratch files on")
                print("           remote machine: " + host)
                
                return "Success"

            else:
                print("    ERROR: Image Link failed.")
            
                return "Fail" 
        else:
            print("     NOTE: DSS images are in use. Skipping statistics.")
        
            return "Success"

    if whichCam == "Guider":
        print("     NOTE: Statstics for the remote guider not yet implemented.")



def getTemp():
#
# Pulls the temperature - used for deciding when to refocus
#
    focTemp = TSXSend("ccdsoftCamera.focTemperature.toFixed(1)")
    timeStamp("Reported temperature is: " + focTemp)
    return float(focTemp)


def hardPark():
#
# Point the mount towards the pole, turn off tracking, disconnect from cameras. Exit
#

    timeStamp("Ending imaging run.")

    stopGuiding()

    TSXSend("sky6StarChart.DocumentProperty(0)")
    latitude = TSXSend("sky6StarChart.DocPropOut")
    
    if float(latitude) < 0:
        print("     NOTE: Pointing mount to the south.")
        slew("HIP112405")
    else:
        print("     NOTE: Pointing mount to the north.")
        slew("kochab")

    if "Paramount" in TSXSend("SelectedHardware.mountModel"):
        if not "Error" in TSXSend("sky6RASCOMTele.ParkAndDoNotDisconnect()"):
            timeStamp("Paramount moved to park position.")
        else:
            timeStamp("No park position set. Stopping sidereal motor.")
            TSXSend("sky6RASCOMTele.SetTracking(0, 1, 0 ,0)")
    else:
        if TSXSend("SelectedHardware.mountModel") !=  "Telescope Mount Simulator":
            print("     NOTE: Turning off sidereal drive.")
            TSXSend("sky6RASCOMTele.SetTracking(0, 1, 0 ,0)")

    timeStamp("Resetting camera defaults.")

    TSXSend("ccdsoftCamera.ExposureTime = 10")		
    TSXSend("ccdsoftCamera.AutoSaveOn = true")
    TSXSend("ccdsoftCamera.Frame = 1")
    TSXSend("ccdsoftCamera.Delay = 0")
    TSXSend("ccdsoftCamera.Subframe = false")

    TSXSend("ccdsoftAutoguider.ExposureTime = 5")
    TSXSend("ccdsoftAutoguider.AutoguiderExposureTime = 5")
    TSXSend("ccdsoftAutoguider.AutoSaveOn = false")
    TSXSend("ccdsoftAutoguider.Frame = 1")
    TSXSend("ccdsoftAutoguider.Delay = 0")
    TSXSend("ccdsoftAutoguider.Subframe = false")

    if str(TSXSend('ccdsoftCamera.PropStr("m_csObserver")')) ==  "Ken Sturrock":
        if str(TSXSend("SelectedHardware.cameraModel")) == "ASICamera": 
            TSXSend("ccdsoftCamera.ImageReduction = 0")
            TSXSend("ccdsoftCamera.TemperatureSetPoint = 1")
            TSXSend("ccdsoftCamera.FilterIndexZeroBased = 0")
            TSXSend("ccdsoftCamera.ExposureTime = 5")	
		
        if str(TSXSend("SelectedHardware.cameraModel")) == "QSI Camera  ":
            TSXSend("ccdsoftCamera.ImageReduction = 1")
            TSXSend("ccdsoftCamera.TemperatureSetPoint = 1")
            TSXSend("ccdsoftCamera.FilterIndexZeroBased = 0")

        if str(TSXSend("SelectedHardware.cameraModel")) == "Camera Simulator":
            TSXSend("ccdsoftCamera.FilterIndexZeroBased = 0")

    camDisconnect("Imager")
    camDisconnect("Guider")

    timeStamp("System Parked.")

    sys.exit()



def isDayLight():
#
# Is the sun above 15 degrees? If so, it's light outside.
#

    if TSXSend("ccdsoftCamera.ImageUseDigitizedSkySurvey") != "1":
        TSXSend("sky6ObjectInformation.Property(0)")
        target = TSXSend("sky6ObjectInformation.ObjInfoPropOut")

        if targAlt("Sun") > -15 and targHA("Sun") < 0:
            timeStamp("Good morning.")
            hardPark()

        while targAlt("Sun") > -15 and targHA("Sun") > 0:
            timeStamp("The sky is not yet dark.")
            timeStamp("Waiting five minutes.")
            time.sleep (300)

        TSXSend('sky6StarChart.Find("' + target + '")')


def isGuiderLost(limit):
#
# Report back if the guider is lost
#
    if TSXSend("ccdsoftCamera.ImageUseDigitizedSkySurvey") != "1":
        errorX = TSXSend('ccdsoftAutoguider.GuideErrorX')
        errorY = TSXSend('ccdsoftAutoguider.GuideErrorY')

        errorX = round(float(errorX), 2)
        errorY = round(float(errorY), 2)

        if abs(round(float(errorX), 2)) < (limit * 3) and abs(errorY) < (limit * 3):
            return "No"

        else:
            return "Yes"
    else:
            return "No"

def preRun():
#
# This function checks a few settings that need to be in place before the script is
# run. It uses the "mysterious" variables found in the Imaging Profile INI file.
#
    print ("     NOTE: Checking configuration settings.")

    result = "Success"
    
    if TSXSend('ccdsoftCamera.PropStr("m_csObserver")') == "":
        print("    ERROR: Please fill in observer name in camera settings")
        result = "Fail"

    if TSXSend('ccdsoftCamera.PropDbl("m_dTeleFocalLength")') == "0":
        print("    ERROR: Please fill in telescope focal length in camera settings")
        result = "Fail"

    if TSXSend('ccdsoftAutoguider.PropDbl("m_dTeleFocalLength")') == "0":
        print("    ERROR: Please fill in telescope focal length in guider settings")
        result = "Fail"

    if " " in TSXSend('ccdsoftCamera.PropStr("m_csAutoSavePath")'):
        print("    ERROR: Please remove any spaces in the autosave path under the camera settings")
        result = "Fail"

    if " " in TSXSend('ccdsoftAutoguider.PropStr("m_csAutoSavePath")'):
        print("    ERROR: Please remove any spaces in the autosave path under the guider settings")
        result = "Fail"

    if " " in TSXSend('ccdsoftCamera.PropStr("m_csAutoSaveColonaDateFormat")'):
        print("    ERROR: Please remove any spaces in the date format under the camera settings")
        result = "Fail"

    if " " in TSXSend('ccdsoftAutoguider.PropStr("m_csAutoSaveColonaDateFormat")'):
        print("    ERROR: Please remove any spaces in the date format under the guider settings")
        result = "Fail"

    if TSXSend("SelectedHardware.cameraModel") != "Camera Simulator":
        if TSXSend("ccdsoftCamera.ImageUseDigitizedSkySurvey") == "1":
            print("    ERROR: Non-simulated camera set to use DSS images.")
            result = "Fail"

    if TSXSend("SelectedHardware.autoguiderCameraModel") != "Camera Simulator":
        if TSXSend("ccdsoftAutoguider.ImageUseDigitizedSkySurvey") == "1":
            print("    ERROR: Non-simulated guider set to use DSS images.")
            result = "Fail"

    TSXSend('ccdsoftCamera.setPropLng("m_bAutoSaveNoWhiteSpace", 1)')
    TSXSend('ccdsoftAutoguider.setPropLng("m_bAutoSaveNoWhiteSpace", 1)')
    TSXSend('ccdsoftAutoguider.setPropLng("m_bShowAutoguider", 1)')

    return result

def remoteImageDone(host, whichCam):
#
# This checks to see if the remote image is complete.
#

    if whichCam not in ("Imager", "Guider"):
        print("   ERROR: Please specify camera as either: Imager or Guider.")
        print("          ASSuming imaging camera.")
        whichCam = "Imager"

    if whichCam == "Imager":
        timeStamp("Checking remote imaging camera status.")

        camStatus = TSXSendRemote(host,"ccdsoftCamera.Status")
        while camStatus != "Ready":
            print("     NOTE: Status: "+ camStatus)
            print("     NOTE: Waiting.")
            time.sleep(10)
            camStatus = TSXSendRemote(host,"ccdsoftCamera.Status")


    if whichCam == "Guider":
        timeStamp("Checking remote guiding camera status.")

        camStatus = TSXSendRemote(host,"ccdsoftAutoguider.Status")
        while camStatus != "Ready":
            print("     NOTE: Status: "+ camStatus)
            print("     NOTE: Waiting.")
            time.sleep(10)
            camStatus = TSXSendRemote(host,"ccdsoftAutoguider.Status")

    timeStamp("Remote " + whichCam + " is finished.")
        
    

def reSynch():
#
# Resynchronizes the mount position on the skychart
#
# This can be helpful with poor pointing mounts using no pointing model,
# such as my Takahashi.
#

    TSXSend("sky6ObjectInformation.Property(0)")
    targetName =  TSXSend("sky6ObjectInformation.ObjInfoPropOut") 

    TSXSend("sky6ObjectInformation.Property(54)")
    targetRA =  TSXSend("sky6ObjectInformation.ObjInfoPropOut")

    TSXSend("sky6ObjectInformation.Property(55)")		
    targetDec = TSXSend("sky6ObjectInformation.ObjInfoPropOut") 

    TSXSend("sky6RASCOMTele.Sync(" + targetRA + ", " + targetDec + ", " + targetName + " )")

    print("     NOTE: Mount resynched.")
   


def settleGuider(limit):
#
# Now, we're going to actually wait for the guider to settle 
# 

    if TSXSend("ccdsoftCamera.ImageUseDigitizedSkySurvey") == "0":
        goodCount = 0
        totalCount = 0
        settled = "No"

        pausePeriod = float(TSXSend("ccdsoftAutoguider.AutoguiderExposureTime")) + float(TSXSend("ccdsoftAutoguider.Delay")) + 1.0

        timeStamp("Guider settle limit set to " + str(limit) + " guider pixels.")

        while settled == "No":

            if TSXSend("ccdsoftAutoguider.State") != "5":
                print("     NOTE: Guider has stopped guiding.")

            time.sleep(pausePeriod)

            errorX = TSXSend('ccdsoftAutoguider.GuideErrorX')
            errorY = TSXSend('ccdsoftAutoguider.GuideErrorY')

            errorX = round(float(errorX), 2)
            errorY = round(float(errorY), 2)

            if abs(errorX) > limit or abs(errorY) > limit:
                goodCount = 0
                totalCount = totalCount + 1

                if totalCount >= 30:
                    settled = "Yes"

                timeStamp("Guider off target. (" + str(errorX) + ", " + str(errorY) + ") " + "(" + str(totalCount) + " of 30)")

            else:
                goodCount = goodCount + 1
                totalCount = totalCount + 1

                timeStamp("Guider ON target. (" + str(errorX) + ", " + str(errorY) + ") " + "(" + str(goodCount) + " of 5)")

            if goodCount >= 5 or totalCount >= 30:
                settled = "Yes"

        if totalCount >= 30:
            if abs(errorX) < (limit * 4) and abs(errorY) < (limit * 4):
                print("     NOTE: Guider not settled but does not appear to be lost.")
                timeStamp("Continuing.")
                return "Settled"

            else:
                timeStamp("Guider appears lost.")
                return "Lost"

        else:
            timeStamp("Continuing.")
            return "Settled"
    else:
        print("     NOTE: Using DSS images. Skipping settle.")
        timeStamp("Continuing.")
        return "Settled"

def slew(target):
# 
# Performs a normal slew to the specificed target.
#

    slewCount = 0

    if "ReferenceError" in str(TSXSend('sky6StarChart.Find("' + target + '")')):
        timeStamp("Target not found.")
        return "Error"

    timeStamp("Slew to " + target + " starting.")


    if TSXSend("sky6RASCOMTele.IsParked()") == "true":
        print("     NOTE: Unparking mount.")
        TSXSend("sky6RASCOMTele.Unpark()")

    if str(TSXSend("SelectedHardware.mountModel") !=  "Telescope Mount Simulator"):
        TSXSend("sky6RASCOMTele.SetTracking(1, 1, 0 ,0)")

    TSXSend("sky6ObjectInformation.Property(54)")
    targetRA =  TSXSend("sky6ObjectInformation.ObjInfoPropOut")

    TSXSend("sky6ObjectInformation.Property(55)")		
    targetDEC = TSXSend("sky6ObjectInformation.ObjInfoPropOut") 

    TSXSend("sky6RASCOMTele.Asynchronous = true")

    TSXSend('sky6RASCOMTele.SlewToRaDec(' +targetRA + ', ' + targetDEC + ', "' + target + '")')
    time.sleep(0.5)
    
    while TSXSend("sky6RASCOMTele.IsSlewComplete") == "0":
        if slewCount > 119:
            print("    ERROR: Mount appears stuck!")
            timeStamp("Sending abort command.")
            sky6RASCOMTele.Abort()
            if TSXSend("SelectedHardware.mountModel") !=  "Telescope Mount Simulator":
                time.sleep(5)
                timeStamp("Trying to stop sidereal motor.")
                TSXSend("sky6RASCOMTele.SetTracking(0, 1, 0 ,0)")
            timeStamp("Stopping script.")    
            sys.exit()
        else:
            print("     NOTE: Slew in progress.")
            slewCount = slewCount + 1
            time.sleep(10)

    if "Process aborted." in TSXSend("sky6RASCOMTele.IsSlewComplete"):
        timeStamp("Script Aborted.")
        sys.exit()

    TSXSend("sky6RASCOMTele.Asynchronous = false")
    timeStamp("Arrived at " + target)

    TSXSend("sky6RASCOMTele.GetAzAlt()")
    mntAz = round(float(TSXSend("sky6RASCOMTele.dAz")), 2)
    mntAlt = round(float(TSXSend("sky6RASCOMTele.dAlt")), 2) 

    print("     NOTE: Mount currently at: " + str(mntAz)  + " az., " + str(mntAlt) + " alt.")


def slewRemote(host, target):
# 
# Performs a normal slew to the specificed target on a remote machine.
#
# The main idea for this routine is to synchronize the simulated mount on a remote
# machine (running real cameras) so that the autosave file labeling correctly identifies the target.
#
# Of course, it could be used to run real hardware if you had the need.
#
    if "ReferenceError" in str(TSXSendRemote(host,'sky6StarChart.Find("' + target + '")')):
        timeStamp("Target not found.")
        return "Error"

    timeStamp("Remote slew to " + target + " on " + host + " (port: " + str(TSXPort) + ") starting.")


    if TSXSendRemote(host,"sky6RASCOMTele.IsParked()") == "true":
        print("     NOTE: Unparking remote mount.")
        TSXSendRemote(host,"sky6RASCOMTele.Unpark()")

    if str(TSXSendRemote(host,"SelectedHardware.mountModel") !=  "Telescope Mount Simulator"):
        TSXSendRemote(host,"sky6RASCOMTele.SetTracking(1, 1, 0 ,0)")

    TSXSendRemote(host,"sky6ObjectInformation.Property(54)")
    targetRA =  TSXSendRemote(host,"sky6ObjectInformation.ObjInfoPropOut")

    TSXSendRemote(host,"sky6ObjectInformation.Property(55)")		
    targetDEC = TSXSendRemote(host,"sky6ObjectInformation.ObjInfoPropOut") 

    TSXSendRemote(host,"sky6RASCOMTele.Asynchronous = true")

    TSXSendRemote(host,'sky6RASCOMTele.SlewToRaDec(' +targetRA + ', ' + targetDEC + ', "' + target + '")')
    time.sleep(0.5)
    
    while TSXSendRemote(host,"sky6RASCOMTele.IsSlewComplete") == "0":
        print("     NOTE: Remote slew in progress.")
        time.sleep(10)

    if "Process aborted." in TSXSendRemote(host,"sky6RASCOMTele.IsSlewComplete"):
        timeStamp("Script Aborted.")
        sys.exit()

    TSXSendRemote(host,"sky6RASCOMTele.Asynchronous = false")
    timeStamp("Remote mount arrived at " + target)

    TSXSendRemote(host,"sky6RASCOMTele.GetAzAlt()")
    mntAz = round(float(TSXSendRemote(host,"sky6RASCOMTele.dAz")), 2)
    mntAlt = round(float(TSXSendRemote(host,"sky6RASCOMTele.dAlt")), 2) 

    print("     NOTE: Remote mount currently at: " + str(mntAz)  + " az., " + str(mntAlt) + " alt.")



def softPark():
#
# This just stops mount tracking without slewing away from target.
#
# It is intended to stop the mount for safety (in case it is unattended)
# but leave it in place so that you can fix the problem. 
#
# Ideally you shouldn't call it if there's a risk of leaving the OTA
# uncovered until morning.
#
    
    if TSXSend("SelectedHardware.mountModel") !=  "Telescope Mount Simulator":
        timeStamp("Pausing sidereal motor.")
        TSXSend("sky6RASCOMTele.SetTracking(0, 1, 0 ,0)")

    print(" ")
    print("     NOTE: Please press Control-C to abort the script and intervene.")
    print(" ")
    print("     NOTE: Otherwise, the system will park in 30 seconds.")
    print(" ")

    time.sleep(30)

    if TSXSend("SelectedHardware.mountModel") !=  "Telescope Mount Simulator":
        TSXSend("sky6RASCOMTele.SetTracking(1, 1, 0 ,0)")

    hardPark()



def startGuiding(exposure, delay, XCoord, YCoord):
#
# Fire up guiding with the guiding camera at the supplied coordinates.
#
    
    # You have to unscale for binning because SkyX will rescale it. 
    newXCoord = float(TSXSend('ccdsoftAutoguider.BinX')) * float(XCoord)  
    newYCoord = float(TSXSend('ccdsoftAutoguider.BinY')) * float(YCoord)

    TSXSend("ccdsoftAutoguider.GuideStarX = " + str(newXCoord))
    TSXSend("ccdsoftAutoguider.GuideStarY = " + str(newYCoord))
    
    TSXSend("ccdsoftAutoguider.AutoSaveOn = false")
    TSXSend("ccdsoftAutoguider.Subframe = false")
    TSXSend("ccdsoftAutoguider.Frame = 1")
    TSXSend("ccdsoftAutoguider.Asynchronous = true")

    TSXSend("ccdsoftAutoguider.AutoguiderExposureTime = " + str(exposure))
    TSXSend("ccdsoftAutoguider.Delay = " + str(delay))

    TSXSend("ccdsoftAutoguider.Autoguide()")

    while TSXSend("ccdsoftAutoguider.State") != "5":
        time.sleep(0.5)

    timeStamp("Autoguiding started.")



def stopGuiding():
#
# This routine clobbers autoguiding.
#
# It has some extra cruft to wait for DSS downloads to complete, which
# throws an error if interrupted, and makes sure that the guiding has
# actually stopped before moving on.
#
    while TSXSend("ccdsoftAutoguider.ExposureStatus") == "DSS From Web":
        time.sleep(0.25)

    TSXSend("ccdsoftAutoguider.Abort()")

    while TSXSend("ccdsoftAutoguider.State") != "0":
        time.sleep(0.5)

    TSXSend("ccdsoftAutoguider.Subframe = false")
    TSXSend("ccdsoftAutoguider.Asynchronous = false")



def takeImage(whichCam, exposure, delay, filterNum):
#
# This function takes an image
# 
# Parameters: Guider or Imager, exposure in seconds, delay in seconds (or NA = leave it alone), which filter number.
#
    if whichCam not in ("Imager", "Guider"):
        print("   ERROR: Please specify camera as either: Imager or Guider.")

    if whichCam == "Imager":
        if TSXSend("SelectedHardware.filterWheelModel") != "<No Filter Wheel Selected>":
            TSXSend("ccdsoftCamera.filterWheelConnect()")	
            if filterNum != "NA":
                TSXSend("ccdsoftCamera.FilterIndexZeroBased = " + filterNum)    
            timeStamp("Imager: " + str(exposure) + "s exposure through " \
            + TSXSend("ccdsoftCamera.szFilterName(" + filterNum + ")") + " filter.")
        else:
            timeStamp("Imager: " + str(exposure) + "s exposure")
    else:
        timeStamp("Guider: " + str(exposure) + "s exposure")

    if whichCam == "Imager":    
        TSXSend("ccdsoftCamera.Asynchronous = false")
        TSXSend("ccdsoftCamera.AutoSaveOn = true")
        TSXSend("ccdsoftCamera.ImageReduction = 0")
        TSXSend("ccdsoftCamera.Frame = 1")
        TSXSend("ccdsoftCamera.Subframe = false")
        TSXSend("ccdsoftCamera.ExposureTime = " + exposure)
        if delay != "NA":
            TSXSend("ccdsoftCamera.Delay = " + delay)

        camMesg = TSXSend("ccdsoftCamera.TakeImage()") 

        if camMesg == "0":

            TSXSend("ccdsoftCameraImage.AttachToActiveImager()")
            cameraImagePath =  TSXSend("ccdsoftCameraImage.Path").split("/")[-1] 
            
            if cameraImagePath == "":
                cameraImagePath = "Image not saved"

            timeStamp("Image completed: " + cameraImagePath)
            return "Success"

        else:
            if "Process aborted." in camMesg:
                timeStamp("Script Aborted.")
                stopGuiding()
                sys.exit()

            timeStamp("Error: " + camMesg)
            return "Fail"

    if whichCam == "Guider": 
        TSXSend("ccdsoftAutoguider.Asynchronous = false")
        TSXSend("ccdsoftAutoguider.AutoSaveOn = true")
        TSXSend("ccdsoftAutoguider.Frame = 1")
        TSXSend("ccdsoftAutoguider.Subframe = false")
        TSXSend("ccdsoftAutoguider.ExposureTime = " + exposure)
        if delay != "NA":
            TSXSend("ccdsoftCamera.Delay = " + delay)
  
        camMesg = TSXSend("ccdsoftAutoguider.TakeImage()")

        if camMesg  == "0":
            TSXSend("ccdsoftAutoguiderImage.AttachToActiveAutoguider()")

            guiderImagePath =  TSXSend("ccdsoftAutoguiderImage.Path").split("/")[-1] 
            
            if guiderImagePath == "":
                guiderImagePath = "Image not saved."

            timeStamp("Guider Image completed: " + guiderImagePath)
            return "Success"

        else:
            if "Process aborted." in camMesg:
                timeStamp("Script Aborted.")
                stopGuiding()
                sys.exit()

            timeStamp("Error: " + camMesg)
            return "Fail"


def takeImageRemote(host, whichCam, exposure, delay, filterNum):
#
# This function takes an image on a remote machine in ASYNC mode.
# 
# Parameters: Host, Guider or Imager, exposure in seconds, delay in seconds (or NA = leave it alone), which filter number.
#

    if whichCam not in ("Imager", "Guider"):
        print("   ERROR: Please specify remote camera as either: Imager or Guider.")

    if whichCam == "Imager":
        if TSXSendRemote(host,"SelectedHardware.filterWheelModel") != "<No Filter Wheel Selected>":
            TSXSendRemote(host,"ccdsoftCamera.filterWheelConnect()")	
            if filterNum != "NA":
                TSXSendRemote(host,"ccdsoftCamera.FilterIndexZeroBased = " + filterNum)    
            timeStamp("Remote Imager: " + str(exposure) + "s exposure through " \
            + TSXSendRemote(host,"ccdsoftCamera.szFilterName(" + filterNum + ")") + " filter.")
        else:
            timeStamp("Remote Imager: " + str(exposure) + "s exposure")
    else:
        timeStamp("Remote Guider: " + str(exposure) + "s exposure")

    if whichCam == "Imager":    
        TSXSendRemote(host,"ccdsoftCamera.Asynchronous = true")
        TSXSendRemote(host,"ccdsoftCamera.AutoSaveOn = true")
        TSXSendRemote(host,"ccdsoftCamera.ImageReduction = 0")
        TSXSendRemote(host,"ccdsoftCamera.Frame = 1")
        TSXSendRemote(host,"ccdsoftCamera.Subframe = false")
        TSXSendRemote(host,"ccdsoftCamera.ExposureTime = " + exposure)
        if delay != "NA":
            TSXSendRemote(host,"ccdsoftCamera.Delay = " + delay)

        TSXSendRemote(host,"ccdsoftCamera.TakeImage()") 

    if whichCam == "Guider": 
        TSXSendRemote(host,"ccdsoftAutoguider.Asynchronous = true")
        TSXSendRemote(host,"ccdsoftAutoguider.AutoSaveOn = true")
        TSXSendRemote(host,"ccdsoftAutoguider.Frame = 1")
        TSXSendRemote(host,"ccdsoftAutoguider.Subframe = false")
        TSXSendRemote(host,"ccdsoftAutoguider.ExposureTime = " + exposure)
        if delay != "NA":
            TSXSendRemote(host,"ccdsoftCamera.Delay = " + delay)
  
        TSXSendRemote(host,"ccdsoftAutoguider.TakeImage()")

    timeStamp("Remote command issued asynchronously.")



def targAlt(target):
#
# Report the altitude of the target.
#
# Useful for determining when to start & stop imaging.
#

    if "ReferenceError" in str(TSXSend('sky6StarChart.Find("' + target + '")')):
        timeStamp("Target not found.")
        return "Error"
    
    TSXSend("sky6ObjectInformation.Property(59)")
    currentAlt = TSXSend("sky6ObjectInformation.ObjInfoPropOut")

    return float(currentAlt)


def targExists(target):
#
# Target can be found by SkyX?
#
    if "not found" in str(TSXSend('sky6StarChart.Find("' + target + '")')):
        timeStamp("Target " + target + " not found.")
        return "No"
    else:
        return "Yes"



def targHA(target):
#
# Report back the Hour Angle of the target.
#
# Useful for figuring out meridian flips and @F2 "buffering" to avoid crossing the 
# meridian and flipping for a focus star.
#
# Can also be used to determine west (positive value) or east (negative value).
#
    if "ReferenceError" in str(TSXSend('sky6StarChart.Find("' + target + '")')):
        timeStamp("Target not found.")
        return "Error"
    
    TSXSend("sky6ObjectInformation.Property(70)")
    currentHA = TSXSend("sky6ObjectInformation.ObjInfoPropOut")

    return float(currentHA)


def timeStamp(message):
#
# This function provides a standard time-stamped output statement
#
	timeStamp = time.strftime("[%H:%M:%S]")
	print(timeStamp, message)

def TSXSend(message):
#
# This function routes generic commands to TSX Pro through a TCP/IP port
#
# The code was originally written by Anat Ruangrassamee but was modified for Python 3
# and further cruded up by Ken Sturrock to make it more vebose and slower.
#
# Set the verbose flag up top to see the messages back & forth to SkyX for debugging 
# purposes.
#

    
    BUFFER_SIZE = 4096

    TSXSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        TSXSocket.connect((TSXHost, TSXPort))
    except ConnectionRefusedError:
        print("   ERROR: Unable to establish a connection.")
        print("       Is SkyX running? Is the TCP Server Listening?")
        sys.exit()


    fullMessage =  "/* Java Script */" + CR + "/* Socket Start Packet */" + CR + CR         \
    + message + ";"                                                                         \
    + CR + CR + "/* Socket End Packet */"

    TSXSocket.send(fullMessage.encode())
    data = TSXSocket.recv(BUFFER_SIZE)

    #
    # This insanity is only needed because SkyX for Windows encodes non-standard ASCII characters
    # in a different manner than the UNIX platforms which will detonate Python when it tries to handle
    # the little circle used to indicate degrees in the getStats() function above.
    #
    if sys.platform == "win32":
        newData = data.decode("latin-1")
    else:
        newData = data.decode("latin-1")
	#newData = data.decode("UTF-8")

    TSXSocket.close()
    if verbose:  
        print()
        print("---------------------------")
        print("Content of TSX Java Script:")
        print("---------------------------")
        print()
        print(fullMessage)
        print()
        print("--------------------------")
        print("Content of Return Message:")
        print("--------------------------")
        print()
        print(newData)
        print()
        print("--------------------------")
        print()

    try:
        retOutput,retError = newData.split("|")
    except ValueError:
        print("    ERROR: No response. Looks like SkyX crashed.")
        sys.exit()

    if "No error." not in retError:
        return retError

    return retOutput

def TSXSendRemote(host, message):
#
# This version sends the message to a remote host & port
#

    if not ":" in host:    
        print("    ERROR: Remote port not set.")
        print("           Please use XXX.XXX.XXX.XXX:YYYY format for IP address and port.")
        sys.exit()

    TSXHost,TSXPort = host.split(":")
    TSXPort = int(TSXPort)

    BUFFER_SIZE = 4096

    TSXSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        TSXSocket.connect((TSXHost, TSXPort))
    except ConnectionRefusedError:
        print("   ERROR: Unable to establish a connection.")
        print("       Is SkyX running? Is the TCP Server Listening?")
        sys.exit()


    fullMessage =  "/* Java Script */" + CR + "/* Socket Start Packet */" + CR + CR         \
    + message + ";"                                                                         \
    + CR + CR + "/* Socket End Packet */"

    TSXSocket.send(fullMessage.encode())
    data = TSXSocket.recv(BUFFER_SIZE)
    if sys.platform == "win32":
        newData = data.decode("latin-1")
    else:
        newData = data.decode("UTF-8")

    TSXSocket.close()
    if verbose:  
        print()
        print("---------------------------")
        print("Content of TSX Java Script:")
        print("---------------------------")
        print()
        print(fullMessage)
        print()
        print("--------------------------")
        print("Content of Return Message:")
        print("--------------------------")
        print()
        print(newData)
        print()
        print("--------------------------")
        print()

    retOutput,retError = newData.split("|")

    if "No error." not in retError:
        return retError

    return retOutput


