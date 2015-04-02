
import webFunctions

import settings
import ScrapePlugins.RetreivalDbBase

import ScrapePlugins.FoolSlide.FoolSlideFetchBase

class FeedLoader(ScrapePlugins.FoolSlide.FoolSlideFetchBase.FoolFeedLoader):

	loggerPath = "Main.Manga.S2.Fl"
	pluginName = "S2 Scans Link Retreiver"
	tableKey = "s2"
	dbName = settings.DATABASE_DB_NAME

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	tableName = "MangaItems"

	urlBase = "http://reader.s2smanga.com/"
	feedUrl = "http://reader.s2smanga.com/directory/{num}/"


if __name__ == '__main__':
	import utilities.testBase as tb

	with tb.testSetup():
		fl = FeedLoader()

		fl.go()
