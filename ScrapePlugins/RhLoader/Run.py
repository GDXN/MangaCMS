

from ScrapePlugins.RhLoader.RhFeedLoader import RhFeedLoader
from ScrapePlugins.RhLoader.RhContentLoader import RhContentLoader

import ScrapePlugins.RunBase

import time

import runStatus


class Runner(ScrapePlugins.RunBase.ScraperBase):
	loggerPath = "Main.Rh.Run"

	pluginName = "RhLoader"


	def _go(self):

		self.log.info("Checking Rh feeds for updates")
		fl = RhFeedLoader()
		fl.go()
		fl.closeDB()

		time.sleep(3)
		#print "wat", cl

		if not runStatus.run:
			return

		cl = RhContentLoader()

		if not runStatus.run:
			return

		todo = cl.retreiveTodoLinksFromDB()

		if not runStatus.run:
			return

		cl.processTodoLinks(todo)
		cl.closeDB()
