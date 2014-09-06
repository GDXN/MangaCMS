

from ScrapePlugins.MjLoader.mjFeedLoader import MjFeedLoader
from ScrapePlugins.MjLoader.mjContentLoader import MjContentLoader

import ScrapePlugins.RunBase

import time

import runStatus


class Runner(ScrapePlugins.RunBase.ScraperBase):
	loggerPath = "Main.Mj.Run"

	pluginName = "MjLoader"


	def _go(self):

		self.log.info("Checking Mj feeds for updates")
		fl = MjFeedLoader()
		fl.go()
		fl.closeDB()

		time.sleep(3)
		#print "wat", cl

		if not runStatus.run:
			return

		cl = MjContentLoader()

		if not runStatus.run:
			return

		todo = cl.retreiveTodoLinksFromDB()

		if not runStatus.run:
			return

		cl.processTodoLinks(todo)
		cl.closeDB()
