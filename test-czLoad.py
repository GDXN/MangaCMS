
import logSetup
if __name__ == "__main__":
	logSetup.initLogging()



import runStatus

from ScrapePlugins.CzLoader.Run import Runner
from ScrapePlugins.CzLoader.czFeedLoader import CzFeedLoader
from ScrapePlugins.CzLoader.czContentLoader import CzContentLoader
import signal

import os.path

def customHandler(signum, stackframe):
	if runStatus.run:
		runStatus.run = False
		print("Telling threads to stop")
	else:
		print("Multiple keyboard interrupts. Raising")
		raise KeyboardInterrupt

def test():

	signal.signal(signal.SIGINT, customHandler)

	# cl = CzFeedLoader()
	# feedItems = cl.getMainItems(onlyRecent=False)
	# cl.processLinksIntoDB(feedItems)
	# cl.closeDB()




	runner = Runner()
	runner.go()


	# cl = CzContentLoader()
	# todo = cl.retreiveTodoLinksFromDB()
	# cl.processTodoLinks(todo)
	# cl.closeDB()



if __name__ == "__main__":
	try:
		test()
	finally:
		import nameTools as nt
		nt.dirNameProxy.stop()

