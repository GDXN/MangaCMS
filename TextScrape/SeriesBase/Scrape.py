
import logSetup
if __name__ == "__main__":
	print("Initializing logging")
	logSetup.initLogging()

import TextScrape.SystemSeriesBase
import urllib.error

class Monitor(TextScrape.SystemSeriesBase.SeriesBase):

	loggerPath = 'Main.Text.Series.Base'
	pluginName = 'SeriesBase'
	plugin_type = 'SeriesBase'


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




