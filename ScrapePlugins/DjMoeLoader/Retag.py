

from ScrapePlugins.DjMoeLoader.djMoeContentLoader import DjMoeContentLoader

import ScrapePlugins.RunBase

class Runner(ScrapePlugins.RunBase.ScraperBase):


	loggerPath = "Main.DjM.Retagger"
	pluginName = "Doujin Moe Retagger"



	def _go(self):

		cl = DjMoeContentLoader()
		cl.retag()
		cl.closeDB()

