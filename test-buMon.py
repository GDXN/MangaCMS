
import sys

if sys.version_info < (3,0):
	print("Sorry, requires Python 3.x, not Python 2.x")
	sys.exit(1)

import logging
import logSetup
import runStatus
import ScrapePlugins.BuMonitor.Run
import ScrapePlugins.BuMonitor.ChangeMonitor
import ScrapePlugins.BuMonitor.MonitorRun

import signal

def customHandler(signum, stackframe):
	print("Got signal: %s, stack-frame %s" % (signum, stackframe))
	print("Telling threads to stop")
	runStatus.run = False                # to stop my code

def test():

	signal.signal(signal.SIGINT, customHandler)

	logSetup.initLogging(logLevel=logging.DEBUG)

	runner = ScrapePlugins.BuMonitor.Run.Runner()
	runner.go()

	# chMon = ScrapePlugins.BuMonitor.ChangeMonitor.BuDateUpdater()
	# chMon.go()
	# chMon.closeDB()

	# # pages = [u'8304', u'4789', u'4788', u'373']

	# cur = chMon.conn.cursor()

	# ret = cur.execute("SELECT dbId, buId FROM MangaSeries WHERE buId IS NOT NULL;")
	# items = ret.fetchall()
	# for item in items:
	# 	pages = chMon.updateItem(*item)
	# 	if not runStatus.run:
	# 		break


	# #runner.loadNewFiles()
	# chMon.closeDB()

	# mon = ScrapePlugins.BuMonitor.MonitorRun.BuWatchMonitor()

	# mon.getAllManga()
	# mon.closeDB()


if __name__ == "__main__":
	test()
