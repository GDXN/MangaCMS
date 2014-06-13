

import ScrapePlugins.RunBase
import ScrapePlugins.MtLoader.Run
import ScrapePlugins.MtMonitor.Run


class Runner(ScrapePlugins.RunBase.ScraperBase):

	loggerPath = "Main.Mt.Base"
	pluginName = "MtBase"


	def _go(self):
		self.log.info("MtBase calling plugins.")

		monitor = ScrapePlugins.MtMonitor.Run.Runner()
		monitor.go()

		loader = ScrapePlugins.MtLoader.Run.Runner()
		loader.go()

		self.log.info("MtBase Finished calling plugins.")




