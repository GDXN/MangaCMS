
import logSetup
if __name__ == "__main__":
	logSetup.initLogging()



import runStatus

from ScrapePlugins.McLoader.Run import Runner
from ScrapePlugins.McLoader.mcFeedLoader import McFeedLoader
from ScrapePlugins.McLoader.mcContentLoader import McContentLoader
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



	# loader = McFeedLoader()
	# loader.go()
	# feedItems = loader.getAllItems()
	# feedItems = loader.getItemPages("http://mngacow.com/50-Million-Km/")
	# loader.log.info("Processing feed Items")

	# loader.processLinksIntoDB(feedItems)


	nt.dirNameProxy.startDirObservers()

	# r = Runner()
	# r.go()

	cl = McContentLoader()
	# links = cl.retreiveTodoLinksFromDB()

	# link = links.pop()
	# cl.getLink(link)
	cl.go()




if __name__ == "__main__":

	signal.signal(signal.SIGINT, customHandler)
	try:
		test()
	finally:
		import nameTools as nt
		nt.dirNameProxy.stop()

