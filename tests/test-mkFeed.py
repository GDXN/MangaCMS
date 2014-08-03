
import logSetup
if __name__ == "__main__":
	logSetup.initLogging()



import runStatus
from ScrapePlugins.MangaMadokami.Run import Runner
from ScrapePlugins.MangaMadokami.mkFeedLoader import MkFeedLoader
from ScrapePlugins.MangaMadokami.mkContentLoader import MkContentLoader
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



	loader = MkFeedLoader()
	# loader.go()


	feedItems = loader.getMainItems()
	print("feed items")
	for item in feedItems:
		print("Item = ", item)
	print("end feed items")

	# # feedItems = loader.getItemsFromContainer("Ore no Kanojo + H", loader.quoteUrl("http://download.japanzai.com/Ore no Kanojo + H/index.php"))
	# # loader.log.info("Processing feed Items")
	# for item in feedItems:
	# 	print("Item", item)

	# loader.processLinksIntoDB(feedItems)
	# loader.closeDB()

	# nt.dirNameProxy.startDirObservers()

	# runner = Runner()
	# runner.go()

	# cl = MkContentLoader()
	# cl.go()



if __name__ == "__main__":

	signal.signal(signal.SIGINT, customHandler)
	try:
		test()
	finally:
		import nameTools as nt
		nt.dirNameProxy.stop()

