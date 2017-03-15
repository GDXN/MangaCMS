
from .Loader import Loader

import ScrapePlugins.RunBase

import time


class Runner(ScrapePlugins.RunBase.ScraperBase):
	loggerPath = "Main.Manga.Mbx.Run"

	pluginName = "MbxLoader"


	def _go(self):

		self.log.info("Checking Manga Box for updates")
		fl = Loader()
		fl.go()




if __name__ == "__main__":
	import utilities.testBase as tb

	with tb.testSetup():

		run = Runner()
		run.go()

