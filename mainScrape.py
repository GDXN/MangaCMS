import sys
if sys.version_info < ( 3, 4):
	# python too old, kill the script
	sys.exit("This script requires Python 3.4 or newer!")

import logging_tree

if __name__ == "__main__":
	import runStatus
	runStatus.preloadDicts = True


import logSetup
import settings
import schemaUpdater.schemaRevisioner

import statusManager
import time

import runStatus
import signal
import nameTools as nt
import activePlugins

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.executors.pool import ProcessPoolExecutor
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.jobstores.memory import MemoryJobStore

import datetime

executors = {
	'main_jobstore': ProcessPoolExecutor(20),
}
job_defaults = {
	'coalesce': True,
	'max_instances': 1
}

jobstores = {

	'transient_jobstore' : MemoryJobStore(),
	'main_jobstore'      : SQLAlchemyJobStore(url='postgresql://{username}:{password}@{address}:5432/{dbname}'.format(
				username=settings.DATABASE_USER,
				password=settings.DATABASE_PASS,
				address=settings.DATABASE_IP,
				dbname=settings.DATABASE_DB_NAME))
}


# Should probably be a lambda? Laaaazy.
def callMod(passMod):
	lut = {}
	for item, dummy_interval in activePlugins.scrapePlugins.values():
		lut[item.__name__] = item
	if not passMod in lut:
		raise ValueError("Callable '%s' is not in the class lookup table: '%s'!" % (passMod, lut))
	module = lut[passMod]
	instance = module.Runner()
	instance.go()


def scheduleJobs(sched, timeToStart):

	jobs = []
	offset = 0
	for key, value in activePlugins.scrapePlugins.items():
		baseModule, interval = value
		jobs.append((key, baseModule, interval, timeToStart+datetime.timedelta(seconds=60*offset)))
		offset += 1

	activeJobs = []

	for jobId, callee, interval, startWhen in jobs:
		jId = callee.__name__
		activeJobs.append(jId)
		if not sched.get_job(jId):
			sched.add_job(callMod,
						args=(callee.__name__, ),
						trigger='interval',
						seconds=interval,
						start_date=startWhen,
						id=jId,
						replace_existing=True,
						jobstore='main_jobstore',
						misfire_grace_time=2**30)


	# hook in the items in nametools things that require periodic update checks:

	for job in sched.get_jobs('main_jobstore'):
		if not job.id in activeJobs:
			sched.remove_job(job.id, 'main_jobstore')

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

		sched.add_job(classInstance.refresh,
					trigger='interval',
					seconds=classInstance.REFRESH_INTERVAL,
					start_date=datetime.datetime.now()+datetime.timedelta(seconds=20+x),
					jobstore='transient_jobstore')

		x += 60*2.5


# Set up any auxilliary crap that needs to be initialized for
# proper system operation, reset database state,
# check/update database schema, etc...
def preflight():
	logSetup.initLogging(logToDb=True)
	schemaUpdater.schemaRevisioner.updateDatabaseSchema()
	statusManager.resetAllRunningFlags()

	nt.dirNameProxy.startDirObservers()


def go():
	preflight()

	sched = BackgroundScheduler(jobstores=jobstores, executors=executors, job_defaults=job_defaults)

	# startTime = datetime.datetime.now()+datetime.timedelta(seconds=60*60)
	# startTime = datetime.datetime.now()+datetime.timedelta(seconds=60*15)
	# startTime = datetime.datetime.now()+datetime.timedelta(seconds=60*5)
	# startTime = datetime.datetime.now()+datetime.timedelta(seconds=20)
	startTime = datetime.datetime.now()+datetime.timedelta(seconds=10)
	scheduleJobs(sched, startTime)
	sched.start()

	# spinwait for ctrl+c, and exit when it's received.
	loops = 0
	while runStatus.run:
		time.sleep(0.1)
		# loops += 1
		# if loops > 100:
		# 	logging_tree.printout()
		# 	loops = 0

	print("Scraper stopping scheduler")
	sched.shutdown()
	nt.dirNameProxy.stop()



def signal_handler(dummy_signal, dummy_frame):
	if runStatus.run:
		runStatus.run = False
		print("Telling threads to stop (mainScrape)")
	else:
		print("Multiple keyboard interrupts. Raising")
		raise KeyboardInterrupt

if __name__ == "__main__":

	signal.signal(signal.SIGINT, signal_handler)
	go()
