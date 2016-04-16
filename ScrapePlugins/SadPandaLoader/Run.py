

from .DbLoader import DbLoader
from .ContentLoader import ContentLoader

import runStatus

import ScrapePlugins.RunBase

class Runner(ScrapePlugins.RunBase.ScraperBase):


	loggerPath = "Main.Manga.SadPanda.Run"
	pluginName = "SadPanda"



	def _go(self):
		fl = DbLoader()
		fl.go()
		fl.closeDB()


		if not runStatus.run:
			return

		cl = ContentLoader()
		cl.go()
		cl.closeDB()


def test():
	import utilities.testBase as tb

	with tb.testSetup(startObservers=False):
		run = Runner()
		run.go()

if __name__ == "__main__":
	test()
