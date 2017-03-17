


from .DbLoader import DbLoader
from .ContentLoader import ContentLoader


import runStatus

import ScrapePlugins.RunBase

class Runner(ScrapePlugins.RunBase.ScraperBase):

	loggerPath = "Main.Manga.DjM.Run"
	pluginName = "DjMoe"

	def _go(self):


		#print "lawl", fl
		fl = DbLoader()
		fl.go()


		if not runStatus.run:
			return

		cl = ContentLoader()
		cl.go()



if __name__ == "__main__":
	import utilities.testBase as tb

	with tb.testSetup():

		run = Runner()
		run.go()
