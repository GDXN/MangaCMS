

from ScrapePlugins.CzLoader.czFeedLoader import CzFeedLoader
from ScrapePlugins.CzLoader.czContentLoader import CzContentLoader

import ScrapePlugins.RunBase

import time

import runStatus


class Runner(ScrapePlugins.RunBase.ScraperBase):
	loggerPath = "Main.Cz.Run"

	pluginName = "CzLoader"


	def _go(self):

		self.log.info("Checking SK feeds for updates")
		fl = CzFeedLoader()
		fl.go()
		fl.closeDB()

		time.sleep(3)
		#print "wat", cl

		if not runStatus.run:
			return

		cl = CzContentLoader()

		if not runStatus.run:
			return

		todo = cl.retreiveTodoLinksFromDB()

		if not runStatus.run:
			return

		cl.processTodoLinks(todo)
		cl.closeDB()
