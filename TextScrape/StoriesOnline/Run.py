


from .Scrape import Scrape

import ScrapePlugins.RunBase



class Runner(ScrapePlugins.RunBase.ScraperBase):
	loggerPath = "Main.StoriesOnline.Run"

	pluginName = "StoriesOnlineScrape"


	def _go(self):

		self.log.info("Checking StoriesOnline for updates")
		scraper = Scrape()
		scraper.crawl()


def test():
	import logSetup
	logSetup.initLogging()
	scrp = Runner()
	scrp.go()
	# scrp.retreiveItemFromUrl(scrp.startUrl)
	# new = gdp.GDocExtractor.getDriveFileUrls('https://drive.google.com/folderview?id=0B-x_RxmzDHegRk5iblp4alZmSkU&usp=sharing')


if __name__ == "__main__":
	test()

