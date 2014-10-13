
import logSetup
if __name__ == "__main__":
	logSetup.initLogging()


import runStatus
runStatus.preloadDicts = False

from ScrapePlugins.FakkuLoader.Run import Runner
from ScrapePlugins.FakkuLoader.fkFeedLoader import FakkuFeedLoader
from ScrapePlugins.FakkuLoader.fkContentLoader import FakkuContentLoader
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


	loader = FakkuFeedLoader()
	loader.resetStuckItems()
	# loader.go()

	# for x in range(1, 5):
	# 	feedItems = loader.getItems(pageOv	erride=x)
	# 	loader.processLinksIntoDB(feedItems)
	# # feedItems = loader.getItemsFromContainer("Ore no Kanojo + H", loader.quoteUrl("http://download.japanzai.com/Ore no Kanojo + H/index.php"))
	# # loader.log.info("Processing feed Items")
	# for item in feedItems:
	# 	print("Item", item)

	# loader.closeDB()

	# runner = Runner()
	# runner.go()


	cl = FakkuContentLoader()
	# cl.retreivalThreads = 1
	cl.go()


if __name__ == "__main__":

	signal.signal(signal.SIGINT, customHandler)
	try:
		test()
	finally:
		import nameTools as nt
		nt.dirNameProxy.stop()

