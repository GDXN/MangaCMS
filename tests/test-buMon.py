
import sys

if sys.version_info < (3,0):
	print("Sorry, requires Python 3.x, not Python 2.x")
	sys.exit(1)

import logSetup
if __name__ == "__main__":
	logSetup.initLogging()


import logging
import runStatus
import ScrapePlugins.M.BuMonitor.Run
import ScrapePlugins.M.BuMonitor.ChangeMonitor
import ScrapePlugins.M.BuMonitor.MonitorRun

import signal

def customHandler(signum, stackframe):
	if runStatus.run:
		runStatus.run = False
		print("Telling threads to stop")
	else:
		print("Multiple keyboard interrupts. Raising")
		raise KeyboardInterrupt
def test():


	signal.signal(signal.SIGINT, customHandler)


	runner = ScrapePlugins.M.BuMonitor.Run.Runner()
	runner.go()

	# chMon = ScrapePlugins.M.BuMonitor.ChangeMonitor.BuDateUpdater()
	# chMon.go()
	# chMon.closeDB()

	# # pages = [u'8304', u'4789', u'4788', u'373']

	# cur = chMon.conn.cursor()

	# ret = cur.execute("SELECT dbId, buId FROM MangaSeries WHERE buId IS NOT NULL;")
	# items = ret.fetchall()
	# print("items", len(items))
	# for item in items:
	# 	pages = chMon.updateItem(*item)
	# 	if not runStatus.run:
	# 		break


	# chMon.closeDB()



	# runner = ScrapePlugins.M.BuMonitor.MonitorRun.BuWatchMonitor()
	# runner.scanRecentlyUpdated()
	# runner.getListNames()
	# runner.go()
	# runner.closeDB()



	# chMon = ScrapePlugins.M.BuMonitor.ChangeMonitor.BuDateUpdater()
	# chMon.go()
	# chMon.closeDB()


	# mon = ScrapePlugins.M.BuMonitor.MonitorRun.BuWatchMonitor()
	# mon.scanRecentlyUpdated()
	# mon.getAllManga()
	# mon.closeDB()


if __name__ == "__main__":
	test()
