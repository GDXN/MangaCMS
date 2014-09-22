


from TextScrape.BakaTsuki.tsukiScrape import TsukiScrape

import ScrapePlugins.RunBase

import time

import runStatus


class Runner(ScrapePlugins.RunBase.ScraperBase):
	loggerPath = "Main.Ts.Run"

	pluginName = "TsukiScrape"


	def _go(self):

		self.log.info("Checking Baka-Tsuki for updates")
		scraper = TsukiScrape()
		scraper.crawl()
