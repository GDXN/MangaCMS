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
# from apscheduler.jobstores.sqlalchemy_store import SQLAlchemyJobStore



import datetime


def scheduleJobs(sched, timeToStart):

	print("Scheduling jobs!")


	def reTagDjMFiles():
		print("Implement DjM Retagger!")


	def reTagMtFiles():
		print("Implement MtMonitored Files Rescanner!")


	jobs = []
	for key, value  in activePlugins.scrapePlugins.items():
		baseModule, interval = value
		jobs.append((baseModule, interval, timeToStart+datetime.timedelta(seconds=60*key)))



	print("Jobs= ")
	for job in jobs:
		print("	", job)
	# jobs = [

	# 	(reTagDjMFiles,      60*60*24*7, timeToStart),
	# 	(reTagMtFiles,       60*60*24*7, timeToStart)
	# ]


	def callGoOnClass(passedModule):
		instance = passedModule.Runner()
		instance.go()



	for callee, interval, startWhen in jobs:

		# print(callee, interval)
		sched.add_interval_job(callGoOnClass, args=(callee, ), seconds=interval, start_date=startWhen)


	# hook in the items in nametools things that require periodic update checks:
	x = 60
	for name, cls in nt.__dict__.items():
		if  isinstance(cls, type) or not hasattr(cls, "NEEDS_REFRESHING"):
			continue
		print("Have item to schedule - ", name, cls, "every", cls.REFRESH_INTERVAL, "seconds.")
		sched.add_interval_job(cls.refresh, seconds=cls.REFRESH_INTERVAL, start_date=datetime.datetime.now()+datetime.timedelta(seconds=20+x))
		x += 60


	# sched.add_interval_job(printWat, seconds=10, start_date='2014-1-1 01:00')



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
