
import webFunctions

import settings
import ScrapePlugins.RetreivalDbBase

import ScrapePlugins.FoolSlide.FoolSlideFetchBase

class FeedLoader(ScrapePlugins.FoolSlide.FoolSlideFetchBase.FoolFeedLoader):



	loggerPath = "Main.Vs.Fl"
	pluginName = "Vortex Scans Link Retreiver"
	tableKey = "vx"
	dbName = settings.dbName

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	tableName = "MangaItems"

	urlBase = "http://reader.vortex-scans.com/"
	feedUrl = urlBase+"reader/list/{num}/"


if __name__ == '__main__':
	import utilities.testBase as tb

	with tb.testSetup():
		fl = FeedLoader()
		# for item in fl.getAllItems():
		# 	print(item)
		fl.go()
