

from .fkFeedLoader import FakkuFeedLoader
from .fkContentLoader import FakkuContentLoader

import ScrapePlugins.RunBase

import time

import runStatus


class Runner(ScrapePlugins.RunBase.ScraperBase):
	loggerPath = "Main.Manga.Fakku.Run"

	pluginName = "FkLoader"


	def _go(self):

		self.log.info("Checking Fakku feeds for updates")
		fl = FakkuFeedLoader()
		fl.go()
		fl.closeDB()

		time.sleep(3)
		#print "wat", cl

		if not runStatus.run:
			return

		cl = FakkuContentLoader()

		if not runStatus.run:
			return

		todo = cl.retreiveTodoLinksFromDB()

		if not runStatus.run:
			return

		cl.processTodoLinks(todo)
		cl.closeDB()


if __name__ == "__main__":
	import utilities.testBase as tb

	with tb.testSetup(startObservers=False):
		mon = Runner()
		mon.go()

