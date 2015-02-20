


from .Scrape import Scrape

import ScrapePlugins.RunBase


class Runner(ScrapePlugins.RunBase.ScraperBase):
	loggerPath = "Main.WpBlogs.Run"

	pluginName = "WordpressBlogScrape"


	def _go(self):

		self.log.info("Checking WordpressBlogs for updates")
		scraper = Scrape()
		scraper.crawl()


def test():
	import logSetup
	logSetup.initLogging()
	scrp = Runner()
	scrp.go()

if __name__ == "__main__":
	test()

