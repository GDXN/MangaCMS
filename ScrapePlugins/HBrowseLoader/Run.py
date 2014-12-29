

from ScrapePlugins.HBrowseLoader.hbrowseDbLoader import HBrowseDbLoader
from ScrapePlugins.HBrowseLoader.hbrowseContentLoader import HBrowseContentLoader

import settings

import runStatus

import ScrapePlugins.RunBase

class Runner(ScrapePlugins.RunBase.ScraperBase):


	loggerPath = "Main.HBrowse.Run"
	pluginName = "H-Browse"



	def _go(self):
		fl = HBrowseDbLoader()
		fl.go()
		fl.closeDB()


		if not runStatus.run:
			return

		cl = HBrowseContentLoader()
		cl.go()
		cl.closeDB()

