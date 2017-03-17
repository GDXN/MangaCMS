


import ScrapePlugins.RunBase
import settings


import ScrapePlugins.M.FoolSlide.FoolSlideFetchBase
import ScrapePlugins.M.FoolSlide.FoolSlideDownloadBase

import time
import runStatus
import webFunctions

DB_KEY     = "cm"
LONG_NAME  = "Canis Major Scanlations"
SHORT_NAME = "CM"
GROUP_NAME = "CanisMajorScanlations"

URL_BASE = "http://cm-scans.shounen-ai.net/"
READER_POSTFIX = "reader/latest/{num}/"

class FeedLoader(ScrapePlugins.M.FoolSlide.FoolSlideFetchBase.FoolFeedLoader):



	loggerPath = "Main.Manga.%s.Fl" % SHORT_NAME
	pluginName = "%s Link Retreiver" % LONG_NAME
	tableKey = DB_KEY
	dbName = settings.DATABASE_DB_NAME

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	tableName = "MangaItems"

	urlBase = URL_BASE
	feedUrl = urlBase+READER_POSTFIX



class ContentLoader(ScrapePlugins.M.FoolSlide.FoolSlideDownloadBase.FoolContentLoader):

	loggerPath = "Main.Manga.%s.Cl" % SHORT_NAME
	pluginName = "%s Content Retreiver" % LONG_NAME
	tableKey = DB_KEY
	dbName = settings.DATABASE_DB_NAME
	tableName = "MangaItems"
	groupName = GROUP_NAME

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	retreivalThreads = 1

	contentSelector = ('article', 'content')



class Runner(ScrapePlugins.RunBase.ScraperBase):
	loggerPath = "Main.Manga.%s.Run" % SHORT_NAME

	pluginName = "%sLoader" % GROUP_NAME

	sourceName = "%s" % GROUP_NAME

	feedLoader = FeedLoader
	contentLoader = ContentLoader


if __name__ == '__main__':
	import utilities.testBase as tb

	with tb.testSetup():
		fl = Runner()

		fl.go()

