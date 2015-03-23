

from ScrapePlugins.BtLoader.btFeedLoader import BtFeedLoader
from ScrapePlugins.BtLoader.btContentLoader import BtContentLoader

import ScrapePlugins.RunBase

import time

import runStatus


class Runner(ScrapePlugins.RunBase.ScraperBase):
	loggerPath = "Main.Manga.Bt.Run"

	pluginName = "BtLoader"


	def _go(self):

		self.log.info("Checking Bt feeds for updates")
		fl = BtFeedLoader()
		fl.go()
		fl.closeDB()

		time.sleep(3)
		#print "wat", cl

		if not runStatus.run:
			return

		cl = BtContentLoader()

		if not runStatus.run:
			return

		todo = cl.retreiveTodoLinksFromDB()

		if not runStatus.run:
			return

		cl.processTodoLinks(todo)
		cl.closeDB()
