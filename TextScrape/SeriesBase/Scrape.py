
import logSetup
if __name__ == "__main__":
	print("Initializing logging")
	logSetup.initLogging()

import TextScrape.MonitorBase
import urllib.error

class Monitor(TextScrape.MonitorBase.MonitorBase):
	tableName = 'book_series'
	loggerPath = 'Main.LNDB.Monitor'
	pluginName = 'LNDBMonitor'
	plugin_type = 'SeriesMonitor'

	seriesMonitor = True

	def go(self):
		# This just ensures the needed table exists.
		pass



def test():
	scrp = Monitor()
	# scrp.scanAllSeries()
	# scrp.updateOutdated()
	scrp.go()
	# scrp.retreiveItemFromUrl(scrp.startUrl)


if __name__ == "__main__":
	test()




