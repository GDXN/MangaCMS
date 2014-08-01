

from ScrapePlugins.McLoader.mcFeedLoader import McFeedLoader
from ScrapePlugins.McLoader.mcContentLoader import McContentLoader

import ScrapePlugins.RunBase

import time

import runStatus


class Runner(ScrapePlugins.RunBase.ScraperBase):
	loggerPath = "Main.Mc.Run"

	pluginName = "McLoader"


	def _go(self):

		self.log.info("Checking Mc feeds for updates")
		fl = McFeedLoader()
		fl.go()
		fl.closeDB()

		time.sleep(3)
		#print "wat", cl

		if not runStatus.run:
			return

		cl = McContentLoader()

		if not runStatus.run:
			return

		todo = cl.retreiveTodoLinksFromDB()

		if not runStatus.run:
			return

		cl.processTodoLinks(todo)
		cl.closeDB()
