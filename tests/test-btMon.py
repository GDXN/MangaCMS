
import logSetup
if __name__ == "__main__":
	logSetup.initLogging()



import runStatus
from ScrapePlugins.M.BtSeriesFetcher.Run   import Runner
from ScrapePlugins.M.BtSeriesFetcher.btSeriesLoader   import BtSeriesLoader
from ScrapePlugins.M.BtSeriesFetcher.btSeriesEnqueuer import BtSeriesEnqueuer
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

	nt.dirNameProxy.startDirObservers()

	# sMon = BtSeriesLoader()
	# sMon.scanForSeries(rangeOverride=1510)
	# sMon.go()



	# loader = BtFeedLoader()
	# feedItems = loader.getMainItems(rangeOverride=125, rangeOffset=100)
	# loader.log.info("Processing feed Items")

	# loader.processLinksIntoDB(feedItems)


	# cl = BtSeriesEnqueuer()
	# cl.go()

	run = Runner()
	run.go()




if __name__ == "__main__":

	signal.signal(signal.SIGINT, customHandler)
	try:
		test()
	finally:
		import nameTools as nt
		nt.dirNameProxy.stop()

