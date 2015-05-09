


from .Scrape import Scrape

import ScrapePlugins.RunBase

import time

import runStatus


class Runner(ScrapePlugins.RunBase.ScraperBase):
	loggerPath = "Main.Text.ReMonWiki.Run"

	pluginName = "ReMonWikiScrape"


	def _go(self):

		self.log.info("Checking ReMonWiki for updates")
		scraper = Scrape()
		scraper.crawl()


def test():
	import logSetup
	logSetup.initLogging()
	scrp = Runner()
	scrp.go()

if __name__ == "__main__":
	test()