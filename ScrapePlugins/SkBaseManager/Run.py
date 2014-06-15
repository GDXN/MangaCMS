

import ScrapePlugins.RunBase
import ScrapePlugins.SkLoader.Run
# import ScrapePlugins.SkMonitor.Run


class Runner(ScrapePlugins.RunBase.ScraperBase):

	loggerPath = "Main.Sk.Base"
	pluginName = "SkBase"


	def _go(self):
		self.log.info("SkBase calling plugins.")

		self.log.warning("Implement series monitor!")
		# monitor = ScrapePlugins.MtMonitor.Run.Runner()
		# monitor.go()


		loader = ScrapePlugins.SkLoader.Run.Runner()
		loader.go()

		self.log.info("SkBase Finished calling plugins.")




