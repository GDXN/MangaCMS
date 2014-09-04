
import logSetup
if __name__ == "__main__":
	logSetup.initLogging()

import runStatus
runStatus.preloadDicts = False

import archCleaner

import runStatus

import deduplicator.dupCheck as deduper
from ScrapePlugins.HBrowseLoader.Run import Runner
from ScrapePlugins.HBrowseLoader.hbrowseDbLoader import HBrowseDbLoader
from ScrapePlugins.HBrowseLoader.hbrowseContentLoader import HBrowseContentLoader
import signal

import nameTools as nt

import os.path

def customHandler(signum, stackframe):
	if runStatus.run:
		runStatus.run = False
		print("Telling threads to stop")
	else:
		print("Multiple keyboard interrupts. Raising")
		raise KeyboardInterrupt

def test():

	# nt.dirNameProxy.startDirObservers()
	# runner = Runner()
	# runner.go()

	loader = HBrowseDbLoader()
	# # print("Running")
	# # items = loader.getFeed()
	# # print("items", items)
	# loader.go()

	dat = loader.getFeed()

	# for x in range(10):

	# 	dat = loader.getFeed(pageOverride=x)
	# 	loader.processLinksIntoDB(dat)

	# cl.go()
	# # cl.loginIfNeeded()


	# todo = cl.retreiveTodoLinksFromDB()

	# print("todo:", todo)
	# if not runStatus.run:
	# 	return

	# cl.processTodoLinks(todo)


	# loader.closeDB()



if __name__ == "__main__":

	signal.signal(signal.SIGINT, customHandler)
	try:
		test()
	finally:
		import nameTools as nt
		nt.dirNameProxy.stop()

