
import webFunctions
import settings

import ScrapePlugins.RetreivalDbBase

import ScrapePlugins.FoolSlide.FoolSlideFetchBase

class FeedLoader(ScrapePlugins.FoolSlide.FoolSlideFetchBase.FoolFeedLoader):


	loggerPath = "Main.Se.Fl"
	pluginName = "Sense Scans Link Retreiver"
	tableKey = "se"
	dbName = settings.DATABASE_DB_NAME
	tableName = "MangaItems"


	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	urlBase = "http://reader.sensescans.com/"
	feedUrl = urlBase+"reader/list/{num}/"


if __name__ == '__main__':
	import utilities.testBase as tb

	with tb.testSetup():
		fl = FeedLoader()
		# for item in fl.getAllItems():
		# 	print(item)
		fl.go()
