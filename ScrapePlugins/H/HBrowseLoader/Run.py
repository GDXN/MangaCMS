

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


		if not runStatus.run:
			return

		cl = HBrowseContentLoader()
		cl.go()



if __name__ == "__main__":

	import utilities.testBase as tb

	with tb.testSetup():
		obj = Runner()
		obj.go()
