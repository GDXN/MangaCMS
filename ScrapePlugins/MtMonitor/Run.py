

import ScrapePlugins.RunBase
import ScrapePlugins.MtMonitor.MonitorRun


class Runner(ScrapePlugins.RunBase.ScraperBase):

	loggerPath = "Main.Mt.Mon"
	pluginName = "MtMonitor"

	def _go(self):


		runner = ScrapePlugins.MtMonitor.MonitorRun.MtWatchMonitor()
		runner.go()
		self.log.info("MtMon Finished Checking Older lists.")
		runner.closeDB()



