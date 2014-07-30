

from ScrapePlugins.BtSeriesFetcher.btSeriesLoader   import BtSeriesLoader
from ScrapePlugins.BtSeriesFetcher.btSeriesEnqueuer import BtSeriesEnqueuer

import ScrapePlugins.RunBase

import time

import runStatus


class Runner(ScrapePlugins.RunBase.ScraperBase):
	loggerPath = "Main.BtS.Run"

	pluginName = "BtLoader"


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
