
import logSetup
if __name__ == "__main__":
	logSetup.initLogging()

import archCleaner

import runStatus

import deduplicator.dupCheck as deduper
from ScrapePlugins.PururinLoader.Run import Runner
from ScrapePlugins.PururinLoader.pururinDbLoader import PururinDbLoader
from ScrapePlugins.PururinLoader.pururinContentLoader import PururinContentLoader
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

	# loader = PururinDbLoader()
	# # print("Running")
	# # items = loader.getFeed()
	# # print("items", items)
	# # loader.go()

	# for x in range(10):

	# 	dat = loader.getFeed(pageOverride=x)
	# 	loader.processLinksIntoDB(dat)



	checker1 = deduper.ArchChecker('/media/Storage/Scripts/MangaCMS/test/test1.zip')
	checker2 = deduper.ArchChecker('/media/Storage/Scripts/MangaCMS/test/test2.zip')

	h1 = checker1.getHashes()
	h2 = checker2.getHashes()

	print(h1)
	print(h2)

	'''
	cl = PururinContentLoader()

	rows = cl.getRowsByValue(dlState=2)
	for row in rows:
		if not "deleted" in row:
			fileN = os.path.join(row["downloadPath"], row["fileName"])
			if not fileN:
				print("Archive does not exist? Wat?")
				print(fileN)
				continue
			print(os.path.exists(fileN), fileN)

			checker = deduper.ArchChecker(fileN)
			checker.checkPhash()

			if not runStatus.run:
				print("Exiting!")
				break

	'''
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

