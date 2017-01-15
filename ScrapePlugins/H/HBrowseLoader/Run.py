

from .hbrowseDbLoader import HBrowseDbLoader
from .hbrowseContentLoader import HBrowseContentLoader

import settings

import runStatus

import ScrapePlugins.RunBase

class Runner(ScrapePlugins.RunBase.ScraperBase):


	loggerPath = "Main.Manga.HBrowse.Run"
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



if __name__ == "__main__":

	import utilities.testBase as tb

	with tb.testSetup(startObservers=False):
		obj = Runner()
		obj.go()
