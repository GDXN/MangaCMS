


from TextScrape.Yoraikun.Scrape import Scrape

import ScrapePlugins.RunBase


class Runner(ScrapePlugins.RunBase.ScraperBase):
	loggerPath = "Main.Iml.Run"

	pluginName = "ImoutoliciousScrape"


	def _go(self):

		self.log.info("Checking Imoutolicious for updates")
		scraper = Scrape()
		scraper.crawl()


def test():
	import logSetup
	logSetup.initLogging()
	scrp = Runner()
	scrp.go()


if __name__ == "__main__":
	test()

