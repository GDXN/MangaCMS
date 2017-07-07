

import runStatus
import ScrapePlugins.M.FoolSlide.FoolSlideDownloadBase
import ScrapePlugins.M.FoolSlide.FoolSlideFetchBase


import ScrapePlugins.RunBase
import settings
import time
import webFunctions

class FeedLoader(ScrapePlugins.M.FoolSlide.FoolSlideFetchBase.FoolFeedLoader):


	loggerPath = "Main.Manga.Sj.Fl"
	pluginName = "Shoujo Sense Scans Link Retreiver"
	tableKey = "sj"
	dbName = settings.DATABASE_DB_NAME
	tableName = "MangaItems"


	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	urlBase = "http://reader.shoujosense.com/"
	feedUrl = urlBase+"latest/{num}/"

class ContentLoader(ScrapePlugins.M.FoolSlide.FoolSlideDownloadBase.FoolContentLoader):


	loggerPath = "Main.Manga.Sj.Cl"
	pluginName = "Shoujo Sense Scans Content Retreiver"
	tableKey = "sj"
	dbName = settings.DATABASE_DB_NAME
	tableName = "MangaItems"
	groupName = "ShoujoSense"

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	retreivalThreads = 1

	contentSelector = ('article', 'content')

class Runner(ScrapePlugins.RunBase.ScraperBase):
	loggerPath = "Main.Manga.Sj.Run"

	pluginName = "ShoujoSense"


	sourceName = "ShoujoSense"

	feedLoader = FeedLoader
	contentLoader = ContentLoader


if __name__ == '__main__':
	import utilities.testBase as tb

	with tb.testSetup():
		fl = Runner()

		fl.go()

