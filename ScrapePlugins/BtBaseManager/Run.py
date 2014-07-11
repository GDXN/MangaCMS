

import ScrapePlugins.RunBase
import ScrapePlugins.BtLoader.Run


class Runner(ScrapePlugins.RunBase.ScraperBase):

	loggerPath = "Main.Bt.Base"
	pluginName = "BtBase"


	def _go(self):
		self.log.info("BtBase calling plugins.")

		self.log.warning("Implement series monitor!")
		# monitor = ScrapePlugins.MtMonitor.Run.Runner()
		# monitor.go()


		loader = ScrapePlugins.BtLoader.Run.Runner()
		loader.go()

		self.log.info("BtBase Finished calling plugins.")




