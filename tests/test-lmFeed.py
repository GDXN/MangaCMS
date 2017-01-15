
import logSetup
if __name__ == "__main__":
	logSetup.initLogging()


import runStatus
runStatus.preloadDicts = False

from ScrapePlugins.M.LoneMangaLoader.LmFeedLoader import LmFeedLoader

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



	loader = LmFeedLoader()
	# # loader.getSeriesUrls()
	# items = loader.getItemPages('http://lonemanga.com/manga/gun/')
	# print(items)
	loader.go()


	loader.closeDB()




if __name__ == "__main__":

	signal.signal(signal.SIGINT, customHandler)
	try:
		test()
	finally:
		import nameTools as nt
		nt.dirNameProxy.stop()

