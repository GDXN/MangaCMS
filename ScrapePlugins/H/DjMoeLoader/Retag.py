

from ScrapePlugins.H.DjMoeLoader.ContentLoader import ContentLoader

import ScrapePlugins.RunBase

class Runner(ScrapePlugins.RunBase.ScraperBase):


	loggerPath = "Main.Manga.DjM.Retagger"
	pluginName = "Doujin Moe Retagger"

	def _go(self):
		cl = ContentLoader()
		cl.retag()

