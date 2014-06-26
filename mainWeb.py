
import sys
if sys.version_info < ( 3, 4):
	# python too old, kill the script
	sys.exit("This script requires Python 3.4 or newer!")

import schemaUpdater.schemaRevisioner
schemaUpdater.schemaRevisioner.verifySchemaUpToDate()


import logSetup
logSetup.initLogging()

import time

import runStatus
import signal
# from apscheduler.jobstores.sqlalchemy_store import SQLAlchemyJobStore

import webserver_process


def signal_handler(dummy_signal, dummy_frame):
	if runStatus.run:
		runStatus.run = False
		print("Telling threads to stop")
	else:
		print("Multiple keyboard interrupts. Raising")
		raise KeyboardInterrupt

if __name__ == "__main__":

	# signal.signal(signal.SIGINT, signal_handler)
	webserver_process.serverProcess()
