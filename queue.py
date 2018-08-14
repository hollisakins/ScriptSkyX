import PySkyX_ks as tsx
from time import sleep

tsx.TSXHost = "10.71.4.5"
tsx.TSXPort = 3040

print('Attempting connection to SkyX at %s:%s' % (tsx.TSXHost,tsx.TSXPort))

camera = "Imager"
Red = "0"
Green = "1"
Blue = "2"
R = "3"
V = "4"
B = "5"
Halpha = "6"
Lum = "7"

numTargets = input('How many targets? ')
targets = []
for i in range(int(numTargets)):
	while True:
		aTarget = input('  %s: ' % str(i+1))
		if tsx.targExists(aTarget)=='Yes':
			targets.append(aTarget)
			break

exptime = "5"
delay = "0"



for target in targets:
	tsx.slew(target)
	sleep(1)
	tsx.takeImage(camera,exptime,delay,V)
	sleep(1)
	#tsx.getStats()
	print('Saved file to %s' % tsx.getActiveImagePath())



