
import logSetup
if __name__ == "__main__":
	logSetup.initLogging()



import runStatus
runStatus.preloadDicts = False
import runStatus


from ScrapePlugins.M.IrcGrabber.EgScans.EgScrape                import EgTriggerLoader
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


	cl = EgTriggerLoader()
	# cl.getMainItems()
	cl.go()


if __name__ == "__main__":
	try:
		test()
	finally:
		import nameTools as nt
		nt.dirNameProxy.stop()

