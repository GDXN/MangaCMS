

from ScrapePlugins.MbLoader.mbFeedLoader import MbFeedLoader
from ScrapePlugins.MbLoader.mbContentLoader import MbContentLoader

import ScrapePlugins.RunBase

import time

import runStatus


class Runner(ScrapePlugins.RunBase.ScraperBase):
	loggerPath = "Main.Mb.Run"

	pluginName = "MbLoader"


	def _go(self):

		self.log.info("Checking MB feeds for updates")
		fl = MbFeedLoader()
		fl.go()
		fl.closeDB()

		time.sleep(3)
		#print "wat", cl

		if not runStatus.run:
			return

		cl = MbContentLoader()

		if not runStatus.run:
			return

		todo = cl.retreiveTodoLinksFromDB()

		if not runStatus.run:
			return

		cl.processTodoLinks(todo)
		cl.closeDB()
