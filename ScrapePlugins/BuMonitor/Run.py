
import ScrapePlugins.BuMonitor.MonitorRun
import ScrapePlugins.BuMonitor.ChangeMonitor
import ScrapePlugins.RunBase

class Runner(ScrapePlugins.RunBase.ScraperBase):

	loggerPath = "Main.Bu.Mon"
	pluginName = "BuMon"

	def _go(self):


		runner = ScrapePlugins.BuMonitor.MonitorRun.BuWatchMonitor()
		runner.go()
		runner.closeDB()



		chMon = ScrapePlugins.BuMonitor.ChangeMonitor.BuDateUpdater()
		chMon.go()
		chMon.closeDB()





if __name__ == "__main__":
	import utilities.testBase as tb

	with tb.testSetup(startObservers=False):
		mon = Runner()
		mon.go()

