
import logSetup
if __name__ == "__main__":
	logSetup.initLogging()



import runStatus

from ScrapePlugins.IrcGrabber.ViScans.ViScrape import ViTriggerLoader
from ScrapePlugins.IrcGrabber.IMangaScans.ImsScrape import IMSTriggerLoader
from ScrapePlugins.IrcGrabber.StupidCommotion.StupidCommotionQueue import StupidCommotionTriggerLoader
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


	cl = ViTriggerLoader()
	cl.go()

	cl = IMSTriggerLoader()
	cl.go()

	cl = StupidCommotionTriggerLoader()
	# cl.getMainItems()
	cl.go()


if __name__ == "__main__":
	try:
		test()
	finally:
		import nameTools as nt
		nt.dirNameProxy.stop()

