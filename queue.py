import PySkyX_ks as tsx
from time import sleep
from datetime import datetime
import traceback
from astropy.coordinates import SkyCoord,FK5
from astropy import units as u
from time import strftime,localtime


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

def sendMsg(message):
	from email.MIMEMultipart import MIMEMultipart
	import smtplib
	from email.MIMEText import MIMEText

	s = smtplib.SMTP('smtp.gmail.com', 587)
	s.starttls()
	address = 'gcdatapipeline@gmail.com' 
	password = '**Mintaka'
	s.login(address,password)
	msg = MIMEMultipart()
	msg['From'] = 'Guilford College Cline Observatory'
	msg['Subject'] = "Fatal Error: Scripted Observer %s" % strftime("%Y-%m-%d", localtime())

	body = '''
	Fatal Error in Scripted Observing:\n
	\n
	%s
	''' % message
	
	msg.attach(MIMEText(body, 'plain'))
	text = msg.as_string()

	recipients = ['hollis.akins@gmail.com']

	for recipient in recipients:
		msg['To'] = recipient
		s.sendmail(address,recipient,text)
	s.quit()

try:
	tsx.TSXHost = "10.71.4.5"
	tsx.TSXPort = 3040
	print('Attempting connection to SkyX at %s:%s' % (tsx.TSXHost,tsx.TSXPort))
	print('')

	# fill in with several targets and their corresponding filters and exposure times
	targnames = ['V0457-Lac','WASP-93','WASP-135','kepler-840','kepler-686']
	# topocentric coordinates not J2000---coordiates ON DATE
	targets_j2000 = [
		('22h36m22.9860296424s','+38d06m18.368386078s'),
		('00h37m50.1100065561s','+51d17m19.559072949s'),
		('17h49m08.40s','+29d52m44.9s'),
		('19h46m01.7684787984s','+49d27m26.238469580s'),
		('19h00m51.3164323877s','+39d01m38.812046717s')
	]
	targets = []
	for target in targets_j2000:
		coords = SkyCoord(str(target[0]), str(target[1]), frame=FK5)
		j2018 = FK5(equinox='J2018.6274')  # String initializes an astropy.time.Time object
		coords = coords.transform_to(j2018)  
		targets.append((coords.ra.hour,coords.dec.degree))

	# Red = "0", Green = "1", Blue = "2", R = "3", V = "4", B = "5", Halpha = "6", Lum = "7"
	filters = ['4','4','4','4','4']
	exptimes = ['120','120','120','120','120']
	# not sure if there is functionality to set binning but I think 3x3 is fine for now

	# make sure that all the targets exist in the database before we try to slew to any
	# for target in targets:
	# 	if not tsx.targExists(target)=='Yes':
	# 		print("Target %s does not exist in SkyX database, please re-enter" % target)
	# 		raise KeyboardInterrupt

	# define end time for the script to auto shutdown
	endtime = "2018-08-17 05:00"
	print("Script will begin shutdown at %s" % endtime)
	endtime = datetime.strptime(endtime,"%Y-%m-%d %H:%M")
		
	# start up the observatory!
	startup()

	IsNightTime = True # will change to false after endtime has passed
	
	while IsNightTime: # while still true
		now = datetime.now() # redefine now each time
		for target,filt,exptime,targname in zip(targets,filters,exptimes,targnames): # for each target and its correspoding exptime and filter
			tsx.slewToCoords(target,targname)
			tsx.takeImage(camera,exptime,'1',filt) # take image
			path = tsx.getActiveImagePath() # get path
			print("Saved image to %s" % path)
			tsx.getStatsPath(path) # image link at that path
			# then do it again if IsNightTime is still true
		if now >= end: # if we have passed end time
			print('After %s, beginning shut down procedures' % endtime) 
			IsNightTime = False # change isNightTime to false to break while loop

	shutdown() # shutdown the observatory 
	print('Complete!')

except KeyboardInterrupt:
    raise

except:
	tb = traceback.format_exc()
	sendMsg(tb)
	raise 
