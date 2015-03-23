
import webFunctions

import settings
import ScrapePlugins.RetreivalDbBase

import ScrapePlugins.FoolSlide.FoolSlideFetchBase

class FeedLoader(ScrapePlugins.FoolSlide.FoolSlideFetchBase.FoolFeedLoader):



	loggerPath = "Main.Manga.Rh.Fl"
	pluginName = "RedHawk Scans Link Retreiver"
	tableKey = "rh"
	dbName = settings.DATABASE_DB_NAME

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	tableName = "MangaItems"

	urlBase = "http://manga.redhawkscans.com/"
	feedUrl = "http://manga.redhawkscans.com/reader/list/{num}/"


if __name__ == '__main__':
	import utilities.testBase as tb

	with tb.testSetup():
		fl = FeedLoader()

		fl.go()
