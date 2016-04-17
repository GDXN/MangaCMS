


from .djMoeDbLoader import DjMoeDbLoader
from .djMoeContentLoader import DjMoeContentLoader


import runStatus

import ScrapePlugins.RunBase

class Runner(ScrapePlugins.RunBase.ScraperBase):

	loggerPath = "Main.Manga.DjM.Run"
	pluginName = "DjMoe"

	def _go(self):


		#print "lawl", fl
		fl = DjMoeDbLoader()
		fl.go()
		fl.closeDB()


		if not runStatus.run:
			return

		cl = DjMoeContentLoader()
		cl.go()
		cl.closeDB()



if __name__ == "__main__":
	import utilities.testBase as tb

	with tb.testSetup():

		run = Runner()
		run.go()
