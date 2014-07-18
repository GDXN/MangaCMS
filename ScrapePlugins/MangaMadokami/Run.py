

from ScrapePlugins.MangaMadokami.mkFeedLoader import MkFeedLoader
from ScrapePlugins.MangaMadokami.mkContentLoader import MkContentLoader

import ScrapePlugins.RunBase

import time

import runStatus


class Runner(ScrapePlugins.RunBase.ScraperBase):
	loggerPath = "Main.Mk.Run"

	pluginName = "MkLoader"


	def _go(self):

		self.log.info("Checking Mk feeds for updates")
		fl = MkFeedLoader()
		fl.go()
		fl.closeDB()

		time.sleep(3)
		#print "wat", cl

		if not runStatus.run:
			return

		cl = MkContentLoader()

		if not runStatus.run:
			return

		todo = cl.retreiveTodoLinksFromDB()

		if not runStatus.run:
			return

		cl.processTodoLinks(todo)
		cl.closeDB()
