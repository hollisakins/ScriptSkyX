import PySkyX_ks as tsx
from time import sleep

tsx.TSXHost = "10.71.4.5"
tsx.TSXPort = 3040

print('Attempting connection to SkyX at %s:%s' % (tsx.TSXHost,tsx.TSXPort))

camera = "Imager"
targetIdentified = False
while not targetIdentified:
	target = str(raw_input('Target name: '))
	if tsx.targExists(target)=='Yes':
		print('Slewing to target %s' % target)
		targetIdentified = True
	else:
		print('Target not found in SkyX database')

tsx.slew(target)
print('')
num = str(raw_input('How many images do you want to take? '))
print('')
exptime = str(raw_input('Exposure time of each image in seconds? '))
print('')
delay = str(raw_input('Delay between each image in seconds? '))
print('')
print('Red = "0", Green = "1", Blue = "2", R = "3", V = "4", B = "5", Halpha = "6", Lum = "7"')
filt = str(raw_input('Filter for each image (number)? '))
print('')

sleep(1)
for i in range(int(num)):
	tsx.takeImage(camera,exptime,delay,filt)
	print('Saved file to %s' % tsx.getActiveImagePath())
	sleep(2)
	path = tsx.getActiveImagePath()
	tsx.getStatsPath(path)



