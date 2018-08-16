import PySkyX_ks as tsx
from time import sleep
from datetime import datetime
import traceback

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
	targets = ['V0457Lac','WASP-93','WASP-135','kepler-840','kepler-686']
	# Red = "0", Green = "1", Blue = "2", R = "3", V = "4", B = "5", Halpha = "6", Lum = "7"
	filters = ['4','4','4','4','4']
	exptimes = ['120','120','120','120','120']
	# not sure if there is functionality to set binning but I think 3x3 is fine for now

	# make sure that all the targets exist in the database before we try to slew to any
	for target in targets:
		if not tsx.targExists(target)=='Yes':
			print("Target %s does not exist in SkyX database, please re-enter" % target)
			raise KeyboardInterrupt

	# define end time for the script to auto shutdown
	endtime = "2018-08-17 05:00"
	print("Script will begin shutdown at %s" % endtime)
	endtime = datetime.strptime(endtime,"%Y-%m-%d %H:%M")
	
	
	# start up the observatory!
	startup()

	IsNightTime = True # will change to false after endtime has passed
	
	while IsNightTime: # while still true
		now = datetime.now() # redefine now each time
		for target,filt,exptime in zip(targets,filters,exptimes): # for each target and its correspoding exptime and filter
			tsx.slew(target) # slew to the target
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