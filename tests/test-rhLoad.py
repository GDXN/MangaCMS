
import logSetup
if __name__ == "__main__":
	logSetup.initLogging()


import runStatus
runStatus.preloadDicts = False

from ScrapePlugins.RhLoader.Run import Runner
from ScrapePlugins.RhLoader.RhFeedLoader import RhFeedLoader
from ScrapePlugins.RhLoader.RhContentLoader import RhContentLoader

import signal
import time
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



	# loader = MkFeedLoader()
	# loader.go()


	# feedItems = loader.getMainItems()
	# print("feed items")
	# for item in feedItems:
	# 	print("Item = ", item)
	# # feedItems = loader.getItemsFromContainer("Ore no Kanojo + H", loader.quoteUrl("http://download.japanzai.com/Ore no Kanojo + H/index.php"))
	# # loader.log.info("Processing feed Items")
	# for item in feedItems:
	# 	print("Item", item)

	# loader.processLinksIntoDB(feedItems)
	# loader.closeDB()

	nt.dirNameProxy.startDirObservers()

	runner = Runner()
	runner.go()

	# cl = RhContentLoader()

	# link = {'dbId': 284780,
	# 		'fileName': None,
	# 		'downloadPath': None,
	# 		'lastUpdate': 0.0,
	# 		'sourceUrl': 'http://manga.redhawkscans.com/reader/read/kimi_no_iru_machi/en/0/94/',
	# 		'flags': None,
	# 		'seriesName': 'Kimi no Iru Machi',
	# 		'dlState': 0,
	# 		'note': None,
	# 		'originName': 'Kimi no Iru Machi - Chapter 94',
	# 		'tags': None,
	# 		'sourceId': None}

	# cl.getLink(link)

	# links = cl.retreiveTodoLinksFromDB()
	# for link in links:
	# 	print("Link", link)

	# cl.go()



if __name__ == "__main__":

	signal.signal(signal.SIGINT, customHandler)
	try:
		test()
	finally:
		import nameTools as nt
		nt.dirNameProxy.stop()

