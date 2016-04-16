

from .btSeriesLoader   import BtSeriesLoader
from .btSeriesEnqueuer import BtSeriesEnqueuer

import ScrapePlugins.RunBase

import time

import runStatus


class Runner(ScrapePlugins.RunBase.ScraperBase):
	loggerPath = "Main.Manga.BtS.Run"

	pluginName = "BtEnqueue"


	def _go(self):

		self.log.info("Checking Bt feeds for updates")
		fl = BtSeriesLoader()
		fl.go()
		fl.closeDB()

		time.sleep(3)
		#print "wat", cl

		if not runStatus.run:
			return

		cl = BtSeriesEnqueuer()
		cl.go()
		cl.closeDB()


if __name__ == '__main__':
	import utilities.testBase as tb

	with tb.testSetup(startObservers=False):
		run = Runner()

		run.go()
		# fl.go()
