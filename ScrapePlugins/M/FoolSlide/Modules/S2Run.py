

import runStatus
import ScrapePlugins.M.FoolSlide.FoolSlideDownloadBase
import ScrapePlugins.M.FoolSlide.FoolSlideFetchBase


import ScrapePlugins.RunBase
import settings
import time
import webFunctions


class ContentLoader(ScrapePlugins.M.FoolSlide.FoolSlideDownloadBase.FoolContentLoader):



	loggerPath = "Main.Manga.S2.Cl"
	pluginName = "S2 Scans Content Retreiver"
	tableKey = "s2"
	dbName = settings.DATABASE_DB_NAME
	tableName = "MangaItems"
	groupName = "S2Scans"

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	retreivalThreads = 2

	contentSelector = ('article', 'content')


class FeedLoader(ScrapePlugins.M.FoolSlide.FoolSlideFetchBase.FoolFeedLoader):

	loggerPath = "Main.Manga.S2.Fl"
	pluginName = "S2 Scans Link Retreiver"
	tableKey = "s2"
	dbName = settings.DATABASE_DB_NAME

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	tableName = "MangaItems"

	urlBase = "http://reader.s2smanga.com/"
	feedUrl = "http://reader.s2smanga.com/directory/{num}/"

class Runner(ScrapePlugins.RunBase.ScraperBase):
	loggerPath = "Main.Manga.S2.Run"

	pluginName = "S2Loader"

	sourceName = "S2 Scans"

	feedLoader = FeedLoader
	contentLoader = ContentLoader


if __name__ == '__main__':
	import utilities.testBase as tb

	with tb.testSetup():
		fl = Runner()

		fl.go()

