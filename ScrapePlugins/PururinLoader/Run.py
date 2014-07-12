

from ScrapePlugins.PururinLoader.pururinDbLoader import PururinDbLoader
from ScrapePlugins.PururinLoader.pururinContentLoader import PururinContentLoader

import settings

import runStatus

import ScrapePlugins.RunBase

class Runner(ScrapePlugins.RunBase.ScraperBase):


	loggerPath = "Main.Pu.Run"
	pluginName = "Pururin"



	def _go(self):
		fl = PururinDbLoader()
		fl.go()
		fl.closeDB()


		if not runStatus.run:
			return

		cl = PururinContentLoader()
		cl.go()
		cl.closeDB()

