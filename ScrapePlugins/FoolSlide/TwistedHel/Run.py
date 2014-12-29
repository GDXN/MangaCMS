

from ScrapePlugins.FoolSlide.TwistedHel.FeedLoader import FeedLoader
from ScrapePlugins.FoolSlide.TwistedHel.ContentLoader import ContentLoader

import runStatus

import ScrapePlugins.RunBase

class Runner(ScrapePlugins.RunBase.ScraperBase):


	loggerPath = "Main.TwistedHel.Run"
	pluginName = "TwistedHel"



	def _go(self):
		fl = FeedLoader()
		fl.go()
		fl.closeDB()


		if not runStatus.run:
			return

		cl = ContentLoader()
		cl.go()
		cl.closeDB()


if __name__ == "__main__":
	import utilities.testBase as tb

	with tb.testSetup(startObservers=True):
		run = Runner()
		run.go()
