
import logSetup
if __name__ == "__main__":
	logSetup.initLogging()



import runStatus

from ScrapePlugins.CxLoader.Run import Runner
from ScrapePlugins.CxLoader.cxFeedLoader import CxFeedLoader
from ScrapePlugins.CxLoader.cxContentLoader import CxContentLoader
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



	# loader = CxFeedLoader()
	# loader.go()

	# ret = loader.getSeriesUrls()
	# for item in ret:
	# 	print(item)

	# feedItems = loader.getAllItems()
	# feedItems = loader.getItemPages(('http://manga.cxcscans.com/series/bamboo_blade/', 'To Love-Ru Darkness '))
	# loader.log.info("Processing feed Items")

	# loader.processLinksIntoDB(feedItems)


	nt.dirNameProxy.startDirObservers()

	r = Runner()
	r.go()

	# cl = CxContentLoader()
	# links = cl.retreiveTodoLinksFromDB()
	# print("Links")
	# for link in links:
	# 	print("Item", link)
	# link = links.pop()
	# cl.getLink(link)
	# # cl.go()




if __name__ == "__main__":

	signal.signal(signal.SIGINT, customHandler)
	try:
		test()
	finally:
		import nameTools as nt
		nt.dirNameProxy.stop()

