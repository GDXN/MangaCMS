
import logSetup
if __name__ == "__main__":
	logSetup.initLogging()


import runStatus
runStatus.preloadDicts = False

from TextScrape.BakaTsuki.tsukiScrape import TsukiScrape
import signal

import readability.readability
import webFunctions
import bs4
# import nameTools as nt

import os.path

def customHandler(signum, stackframe):
	if runStatus.run:
		runStatus.run = False
		print("Telling threads to stop")
	else:
		print("Multiple keyboard interrupts. Raising")
		raise KeyboardInterrupt

def test():

	scraper = TsukiScrape()
	scraper.crawl()

if __name__ == "__main__":

	signal.signal(signal.SIGINT, customHandler)
	try:
		test()
	finally:
		pass
		# import nameTools as nt
		# nt.dirNameProxy.stop()

