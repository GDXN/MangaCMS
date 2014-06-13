

from ScrapePlugins.FufufuuLoader.fufufuDbLoader import FuFuFuuDbLoader
from ScrapePlugins.FufufuuLoader.fufufuContentLoader import FuFuFuuContentLoader

import ScrapePlugins.RunBase

class Runner(ScrapePlugins.RunBase.ScraperBase):


	loggerPath = "Main.Fu.Retagger"
	pluginName = "FufufuuRetagger"



	def _go(self):

		fl = FuFuFuuDbLoader()
		fl.checkThruCloudFlare()
		cl = FuFuFuuContentLoader()
		cl.retag()
		cl.closeDB()

