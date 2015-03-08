


from .Scrape import Monitor
from .Custom import CustomMonitor

import ScrapePlugins.RunBase


class Runner(ScrapePlugins.RunBase.ScraperBase):
	loggerPath = "Main.SeriesDbBase.Run"

	pluginName = "BookSeriesTableGen"


	def _go(self):

		self.log.info("Creating seriesTables")
		scraper = Monitor()
		scraper.go()
		scraper = CustomMonitor()
		scraper.go()


def test():
	import logSetup
	logSetup.initLogging()
	scrp = Runner()
	scrp.go()

if __name__ == "__main__":
	test()

