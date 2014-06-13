
import logging
import logSetup
import runStatus
import ScrapePlugins.BuMonitor.Run
import ScrapePlugins.BuMonitor.ChangeMonitor

import signal

def customHandler(signum, stackframe):
	print("Got signal: %s, stack-frame %s" % (signum, stackframe))
	print("Telling threads to stop")
	runStatus.run = False                # to stop my code

def test():

	signal.signal(signal.SIGINT, customHandler)

	logSetup.initLogging(logLevel=logging.DEBUG)

	# runner = ScrapePlugins.BuMonitor.Run.Runner()
	# runner.go()

	chMon = ScrapePlugins.BuMonitor.ChangeMonitor.BuDateUpdater()
	chMon.go()
	chMon.closeDB()

	# pages = [u'8304', u'4789', u'4788', u'373']
	#pages = [u'375']
	#pages = runner.getMangaIDs()


	#runner.loadNewFiles()


if __name__ == "__main__":
	test()
