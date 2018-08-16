import PySkyX_ks as tsx
from time import sleep

camera = "Imager"

def startup():
	tsx.openDome()
	tsx.findDomeHome()
	tsx.connectMount()
	tsx.camConnect(camera)

def shutdown():
	tsx.camDisconnect(camera)
	tsx.parkAndDisconnectMount()
	tsx.closeDome()
	tsx.findDomeHome()
	tsx.domeDisconnect()


tsx.TSXHost = "10.71.4.5"
tsx.TSXPort = 3040
print('Attempting connection to SkyX at %s:%s' % (tsx.TSXHost,tsx.TSXPort))
print('')

targets = ['m42','m45','RR Lyr']
# Red = "0", Green = "1", Blue = "2", R = "3", V = "4", B = "5", Halpha = "6", Lum = "7"
filters = ['0','1','2','3']
exptimes = ['2','3','4','5']

for target in targets:
	if not tsx.targExists(target)=='Yes':
		raise Exception("Target %s does not exist in SkyX database, please re-enter")



startup()




tsx.slew(target)
print('')
num = str(raw_input('How many images do you want to take? '))
print('')
exptime = str(raw_input('Exposure time of each image in seconds? '))
print('')
delay = str(raw_input('Delay between each image in seconds? '))
print('')
filt = str(raw_input('Filter for each image (number)? '))
print('')

sleep(1)
for i in range(int(num)):
	tsx.takeImage(camera,exptime,delay,filt)
	print('Saved file to %s' % tsx.getActiveImagePath())
	sleep(2)
	path = tsx.getActiveImagePath()
	tsx.getStatsPath(path)



