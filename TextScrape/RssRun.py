


import ScrapePlugins.RunBase
import FeedScrape.RssMonitor




class Runner(ScrapePlugins.RunBase.ScraperBase):
	loggerPath = "Main.Text.Rss.Run"

	pluginName = "RssMonitor"


	def _go(self):

		self.log.info("Checking Rss Feeds for updates")
		FeedScrape.RssMonitor.test()


def test():
	import logSetup
	logSetup.initLogging()
	scrp = Runner()
	scrp.go()
	# scrp.retreiveItemFromUrl(scrp.startUrl)
	# new = gdp.GDocExtractor.getDriveFileUrls('https://drive.google.com/folderview?id=0B-x_RxmzDHegRk5iblp4alZmSkU&usp=sharing')


if __name__ == "__main__":
	test()

