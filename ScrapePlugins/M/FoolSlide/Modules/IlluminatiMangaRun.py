


import ScrapePlugins.RunBase
import settings

import ScrapePlugins.M.FoolSlide.FoolSlideFetchBase

import ScrapePlugins.M.FoolSlide.FoolSlideDownloadBase

import time
import runStatus
import webFunctions

DB_KEY     = "im"
LONG_NAME  = "Illuminati Manga"
SHORT_NAME = "IM"
GROUP_NAME = "IlluminatiManga"

URL_BASE = "http://reader.manga-download.org/"
READER_POSTFIX = "latest/{num}/"

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

