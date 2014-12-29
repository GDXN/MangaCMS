

from ScrapePlugins.Crunchyroll.DbLoader import DbLoader
from ScrapePlugins.Crunchyroll.ContentLoader import ContentLoader

import runStatus

import ScrapePlugins.RunBase

class Runner(ScrapePlugins.RunBase.ScraperBase):


	loggerPath = "Main.CrunchyRoll.Run"
	pluginName = "CrunchyRoll"



	def _go(self):
		fl = DbLoader()
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
