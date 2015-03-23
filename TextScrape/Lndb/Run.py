


from .Scrape import Monitor

import ScrapePlugins.RunBase


class Runner(ScrapePlugins.RunBase.ScraperBase):
	loggerPath = "Main.Text.LNDB.Run"

	pluginName = "LNDBScrape"


	def _go(self):

		self.log.info("Checking LNDB for updates")
		scraper = Monitor()
		scraper.go()


def test():
	import logSetup
	logSetup.initLogging()
	scrp = Runner()
	scrp.go()

if __name__ == "__main__":
	test()

