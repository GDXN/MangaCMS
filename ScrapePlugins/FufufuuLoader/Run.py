

from ScrapePlugins.FufufuuLoader.fufufuDbLoader import FuFuFuuDbLoader
from ScrapePlugins.FufufuuLoader.fufufuContentLoader import FuFuFuuContentLoader

import settings

import runStatus

import ScrapePlugins.RunBase

class Runner(ScrapePlugins.RunBase.ScraperBase):


	loggerPath = "Main.Fu.Run"
	pluginName = "Fufufuu"



	def _go(self):
		fl = FuFuFuuDbLoader()
		fl.go()
		fl.closeDB()


		if not runStatus.run:
			return

		cl = FuFuFuuContentLoader()
		cl.go()
		cl.closeDB()

