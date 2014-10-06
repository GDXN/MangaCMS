


from TextScrape.ReTranslations.reScrape import ReScrape

import ScrapePlugins.RunBase

import time

import runStatus


class Runner(ScrapePlugins.RunBase.ScraperBase):
	loggerPath = "Main.Re.Run"

	pluginName = "ReScrape"


	def _go(self):

		self.log.info("Checking Re:Translations for updates")
		scraper = ReScrape()
		scraper.crawl()


if __name__ == "__main__":
	import utilities.testBase
	with utilities.testBase.testSetup():
		run = Runner()
		run.go()