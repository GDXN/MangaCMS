
import sys
if sys.version_info < ( 3, 4):
	# python too old, kill the script
	sys.exit("This script requires Python 3.4 or newer!")

import nameTools as nt

if __name__ == "__main__":
	import runStatus
	runStatus.preloadDicts = False


# mainScrape does actual schema updating. We just want to check the version, and bail
# out if it's too old.
import schemaUpdater.schemaRevisioner
schemaUpdater.schemaRevisioner.verifySchemaUpToDate()


import logSetup
logSetup.initLogging()

import webserver_process
import datetime


from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.executors.pool import ProcessPoolExecutor
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.jobstores.memory import MemoryJobStore


executors = {
	'main_jobstore': ThreadPoolExecutor(3),
}
job_defaults = {
	'coalesce': True,
	'max_instances': 1
}

jobstores = {
	'main_jobstore' : MemoryJobStore(),
}

def run_web():

	nt.dirNameProxy.startDirObservers()


	sched = BackgroundScheduler(jobstores=jobstores, executors=executors, job_defaults=job_defaults)
	sched.start()


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
					jobstore='main_jobstore')

		x += 60*2.5


	# It looks like cherrypy installs a ctrl+c handler, so I don't need to.
	webserver_process.serverProcess()


if __name__ == "__main__":
	run_web()