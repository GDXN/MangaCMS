

from .jzFeedLoader import JzFeedLoader
from .jzContentLoader import JzContentLoader

import ScrapePlugins.RunBase

import time

import runStatus


class Runner(ScrapePlugins.RunBase.ScraperBase):
	loggerPath = "Main.Manga.Jz.Run"

	pluginName = "JzLoader"


	def _go(self):

		self.log.info("Checking Jz feeds for updates")
		fl = JzFeedLoader()
		fl.go()
		fl.closeDB()

		time.sleep(3)
		#print "wat", cl

		if not runStatus.run:
			return

		cl = JzContentLoader()

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
		obj = Runner()
		obj.go()

