


from .Scrape import Scrape

import ScrapePlugins.RunBase


class Runner(ScrapePlugins.RunBase.ScraperBase):
	loggerPath = "Main.BlueSilver.Run"

	pluginName = "BlueSilverScrape"


	def _go(self):

		self.log.info("Checking BlueSilver for updates")
		scraper = Scrape()
		scraper.crawl()


def test():
	import logSetup
	logSetup.initLogging()
	scrp = Runner()
	scrp.go()

if __name__ == "__main__":
	test()

