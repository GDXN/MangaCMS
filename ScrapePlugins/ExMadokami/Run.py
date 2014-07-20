

from ScrapePlugins.ExMadokami.emFeedLoader import EmFeedLoader
from ScrapePlugins.ExMadokami.emContentLoader import EmContentLoader

import ScrapePlugins.RunBase

import time

import runStatus


class Runner(ScrapePlugins.RunBase.ScraperBase):
	loggerPath = "Main.Em.Run"

	pluginName = "EmLoader"


	def _go(self):

		self.log.info("Checking Em feeds for updates")
		fl = EmFeedLoader()
		fl.go()
		fl.closeDB()

		time.sleep(3)
		#print "wat", cl

		if not runStatus.run:
			return

		cl = EmContentLoader()

		if not runStatus.run:
			return

		todo = cl.retreiveTodoLinksFromDB()

		if not runStatus.run:
			return

		cl.processTodoLinks(todo)
		cl.closeDB()
