import sys
if sys.version_info < ( 3, 4):
	# python too old, kill the script
	sys.exit("This script requires Python 3.4 or newer!")


import logSetup

import schemaUpdater.schemaRevisioner

import statusManager
import time

import runStatus
import signal
import nameTools as nt
import activePlugins

from apscheduler.scheduler import Scheduler



import datetime


def scheduleJobs(sched, timeToStart):

	print("Scheduling jobs!")

	jobs = []
	for key, value  in activePlugins.scrapePlugins.items():
		baseModule, interval = value
		jobs.append((baseModule, interval, timeToStart+datetime.timedelta(seconds=60*key)))

	print("Jobs= ")
	for job in jobs:
		print("	", job)

	# Should probably be a lambda? Laaaazy.
	def callGoOnClass(passedModule):
		instance = passedModule.Runner()
		instance.go()

	for callee, interval, startWhen in jobs:
		sched.add_interval_job(callGoOnClass, args=(callee, ), seconds=interval, start_date=startWhen)


	# hook in the items in nametools things that require periodic update checks:
	x = 60
	for name, classInstance in nt.__dict__.items():

		# look up all class instances in nameTools. If they have the magic attribute "NEEDS_REFRESHING",
		# that means they support scheduling, so schedule the class in question.
		# To support auto-refreshing, the class needs to define:
		# cls.NEEDS_REFRESHING = {anything, just checked for existance}
		# cls.REFRESH_INTERVAL = {number of seconds between refresh calls}
		# cls.refresh()        = Call to do the refresh operation. Takes no arguments.
		#
		if  isinstance(classInstance, type) or not hasattr(classInstance, "NEEDS_REFRESHING"):
			continue
		print("Have item to schedule - ", name, classInstance, "every", classInstance.REFRESH_INTERVAL, "seconds.")
		sched.add_interval_job(classInstance.refresh, seconds=classInstance.REFRESH_INTERVAL, start_date=datetime.datetime.now()+datetime.timedelta(seconds=20+x))
		x += 60


# Set up any auxilliary crap that needs to be initialized for
# proper system operation, reset database state,
# check/update database schema, etc...
def preflight():
	logSetup.initLogging()
	schemaUpdater.schemaRevisioner.updateDatabaseSchema()
	statusManager.resetAllRunningFlags()

	nt.dirNameProxy.startDirObservers()


def go():
	preflight()


	sched = Scheduler()

	# startTime = datetime.datetime.now()+datetime.timedelta(seconds=60*60)
	# startTime = datetime.datetime.now()+datetime.timedelta(seconds=60*15)
	# startTime = datetime.datetime.now()+datetime.timedelta(seconds=60*5)
	startTime = datetime.datetime.now()+datetime.timedelta(seconds=20)

	scheduleJobs(sched, startTime)

	sched.start()


	# spinwait for ctrl+c, and exit when it's received.
	while runStatus.run:
		time.sleep(0.1)

	print("Scraper stopping scheduler")
	sched.shutdown()
	nt.dirNameProxy.stop()



def signal_handler(dummy_signal, dummy_frame):
	if runStatus.run:
		runStatus.run = False
		print("Telling threads to stop")
	else:
		print("Multiple keyboard interrupts. Raising")
		raise KeyboardInterrupt

if __name__ == "__main__":

	signal.signal(signal.SIGINT, signal_handler)
	go()
