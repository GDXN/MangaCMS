
import webFunctions
import settings

import ScrapePlugins.RetreivalDbBase

import ScrapePlugins.FoolSlide.FoolSlideFetchBase

class FeedLoader(ScrapePlugins.FoolSlide.FoolSlideFetchBase.FoolFeedLoader):


	loggerPath = "Main.Sj.Fl"
	pluginName = "Shoujo Sense Scans Link Retreiver"
	tableKey = "sj"
	dbName = settings.dbName
	tableName = "MangaItems"


	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	urlBase = "http://reader.shoujosense.com/"
	feedUrl = urlBase+"reader/list/{num}/"


if __name__ == '__main__':
	import utilities.testBase as tb

	with tb.testSetup():
		fl = FeedLoader()
		# for item in fl.getAllItems():
		# 	print(item)
		fl.go()
