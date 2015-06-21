

import FeedScrape.InputScrapers.RoyalRoadL.roadScrape
import ScrapePlugins.RunBase



class Runner(ScrapePlugins.RunBase.ScraperBase):
	loggerPath = "Main.Rss.RRL.Run"

	pluginName = "RrlReleaseMon"


	def _go(self):

		self.log.info("Checking RoyalRoadL feeds for updates")
		fetch = FeedScrape.InputScrapers.RoyalRoadL.roadScrape.RoyalRoadLTest()
		fetch.getChanges()



if __name__ == "__main__":

	import utilities.testBase as tb

	with tb.testSetup(startObservers=False):
		obj = Runner()
		obj.go()

