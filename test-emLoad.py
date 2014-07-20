
import logSetup
if __name__ == "__main__":
	logSetup.initLogging()



import runStatus
from ScrapePlugins.ExMadokami.Run import Runner
from ScrapePlugins.ExMadokami.emFeedLoader import EmFeedLoader
from ScrapePlugins.ExMadokami.emContentLoader import EmContentLoader
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



	# loader = EmFeedLoader()
	# for x in range(20):
	# 	items = loader.getApiItems(page=x)
	# 	loader.processLinksIntoDB(items)
	# # loader.go()


	# feedItems = loader.getMainItems()
	# # feedItems = loader.getItemsFromContainer("Ore no Kanojo + H", loader.quoteUrl("http://download.japanzai.com/Ore no Kanojo + H/index.php"))
	# # loader.log.info("Processing feed Items")
	# for item in feedItems:
	# 	print("Item", item)

	# loader.processLinksIntoDB(feedItems)
	# loader.closeDB()

	runner = Runner()
	runner.go()


	# cl = EmContentLoader()
	# # cl.retreiveTodoLinksFromDB()
	# cl.go()



if __name__ == "__main__":

	signal.signal(signal.SIGINT, customHandler)
	try:
		test()
	finally:
		import nameTools as nt
		nt.dirNameProxy.stop()

