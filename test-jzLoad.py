
import logSetup
if __name__ == "__main__":
	logSetup.initLogging()



import runStatus
from ScrapePlugins.JzLoader.Run import Runner
from ScrapePlugins.JzLoader.jzFeedLoader import JzFeedLoader
from ScrapePlugins.JzLoader.jzContentLoader import JzContentLoader
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



	# loader = JzFeedLoader()
	# feedItems = loader.getMainItems()
	# # feedItems = loader.getItemsFromContainer("Ore no Kanojo + H", loader.quoteUrl("http://download.japanzai.com/Ore no Kanojo + H/index.php"))
	# # loader.log.info("Processing feed Items")
	# for item in feedItems:
	# 	print("Item", item)

	# loader.processLinksIntoDB(feedItems)
	# loader.closeDB()

	nt.dirNameProxy.startDirObservers()
	runner = Runner()
	runner.go()


	# cl = JzContentLoader()
	# cl.go()



if __name__ == "__main__":

	signal.signal(signal.SIGINT, customHandler)
	try:
		test()
	finally:
		import nameTools as nt
		nt.dirNameProxy.stop()

