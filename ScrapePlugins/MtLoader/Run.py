

from ScrapePlugins.MtLoader.mtFeedLoader import MtFeedLoader
from ScrapePlugins.MtLoader.mtContentLoader import MtContentLoader

import ScrapePlugins.RunBase

import time

import runStatus


class Runner(ScrapePlugins.RunBase.ScraperBase):
	loggerPath = "Main.Mt.Run"

	pluginName = "MtLoader"


	def _go(self):

		self.log.info("Checking MT feeds for updates")
		fl = MtFeedLoader()
		fl.go()
		fl.closeDB()

		time.sleep(3)
		#print "wat", cl

		if not runStatus.run:
			return

		cl = MtContentLoader()

		if not runStatus.run:
			return

		todo = cl.retreiveTodoLinksFromDB()

		if not runStatus.run:
			return

		cl.processTodoLinks(todo)
		cl.closeDB()
