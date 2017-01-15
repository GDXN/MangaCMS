
import logSetup
if __name__ == "__main__":
	logSetup.initLogging()


import runStatus
runStatus.preloadDicts = False

from ScrapePlugins.M.RhLoader.Run import Runner
from ScrapePlugins.M.RhLoader.RhFeedLoader import RhFeedLoader
from ScrapePlugins.M.RhLoader.RhContentLoader import RhContentLoader
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



	loader = RhFeedLoader()
	loader.go()


	# loader.getAllItems()
	# loader.getItemPages('http://manga.redhawkscans.com/reader/series/white_album/')

	# # feedItems = loader.getItemsFromContainer("Ore no Kanojo + H", loader.quoteUrl("http://download.japanzai.com/Ore no Kanojo + H/index.php"))
	# # loader.log.info("Processing feed Items")
	# for item in feedItems:
	# 	print("Item", item)

	loader.closeDB()

	# nt.dirNameProxy.startDirObservers()

	# runner = Runner()
	# runner.go()

	# cl = RhContentLoader()
	# cl.go()



if __name__ == "__main__":

	signal.signal(signal.SIGINT, customHandler)
	try:
		test()
	finally:
		import nameTools as nt
		nt.dirNameProxy.stop()

