
import logSetup
if __name__ == "__main__":
	logSetup.initLogging()



import runStatus
runStatus.preloadDicts = False

from ScrapePlugins.MjLoader.Run import Runner
from ScrapePlugins.MjLoader.mjFeedLoader import MjFeedLoader
from ScrapePlugins.MjLoader.mjContentLoader import MjContentLoader
import signal

import time
import calendar

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

	# loader = MjFeedLoader()
	# loader.go()

	nt.dirNameProxy.startDirObservers()
	cl = MjContentLoader()

	cl.go()

	# item = {'note': None,
	# 	 'dbId': 266183,
	# 	 'dlState': 0,
	# 	 'downloadPath': None,
	# 	 'fileName': None,
	# 	 'lastUpdate': 0.0,
	# 	 'originName': '---TEST----',
	# 	 'retreivalTime': calendar.timegm((2014, 9, 2, 7, 0, 0, 1, 245, 0)),
	# 	 'seriesName': '00000000000000Test-------',
	# 	 'sourceId': None,
	# 	 'sourceUrl': 'http://mangajoy.com/Saito-kun-wa-Chounouryokusha-Rashii/24',
	# 	 'tags': None,
	# 	 'flags': ''}

	# cl.getLink(item)

	# todo = cl.retreiveTodoLinksFromDB()
	# for item in todo:
	# 	print("item", item)
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

