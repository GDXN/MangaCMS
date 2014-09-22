


from TextScrape.JapTem.japtemScrape import JaptemScrape

import ScrapePlugins.RunBase

import time

import runStatus


class Runner(ScrapePlugins.RunBase.ScraperBase):
	loggerPath = "Main.Jt.Run"

	pluginName = "JapTemScrape"


	def _go(self):

		self.log.info("Checking JapTem for updates")
		scraper = JaptemScrape()
		scraper.crawl()
