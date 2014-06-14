

import ScrapePlugins.RunBase
import ScrapePlugins.SkLoader.Run
# import ScrapePlugins.SkMonitor.Run


class Runner(ScrapePlugins.RunBase.ScraperBase):

	loggerPath = "Main.Sk.Base"
	pluginName = "SkBase"


	def _go(self):
		self.log.info("SkBase calling plugins.")

		monitor = ScrapePlugins.MtMonitor.Run.Runner()
		monitor.go()

		self.log.warning("Implement series monitor!")

		# loader = ScrapePlugins.MtLoader.Run.Runner()
		# loader.go()

		self.log.info("SkBase Finished calling plugins.")




