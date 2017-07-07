


import runStatus
import ScrapePlugins.M.FoolSlide.FoolSlideDownloadBase
import ScrapePlugins.M.FoolSlide.FoolSlideFetchBase


import ScrapePlugins.RunBase
import settings
import settings
import time
import webFunctions

class FeedLoader(ScrapePlugins.M.FoolSlide.FoolSlideFetchBase.FoolFeedLoader):



	loggerPath = "Main.Manga.Vx.Fl"
	pluginName = "Vortex Scans Link Retreiver"
	tableKey = "vx"
	dbName = settings.DATABASE_DB_NAME

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	tableName = "MangaItems"

	urlBase = "http://reader.vortex-scans.com/"
	feedUrl = urlBase+"latest/{num}/"

class ContentLoader(ScrapePlugins.M.FoolSlide.FoolSlideDownloadBase.FoolContentLoader):




	loggerPath = "Main.Manga.Vx.Cl"
	pluginName = "Vortex Scans Content Retreiver"
	tableKey = "vx"
	dbName = settings.DATABASE_DB_NAME
	tableName = "MangaItems"
	groupName = "VortexScans"

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	retreivalThreads = 1

	contentSelector = ('article', 'content')

class Runner(ScrapePlugins.RunBase.ScraperBase):
	loggerPath = "Main.Manga.Vx.Run"

	pluginName = "VortexLoader"

	sourceName = "Vortex Scans"

	feedLoader = FeedLoader
	contentLoader = ContentLoader


if __name__ == '__main__':
	import utilities.testBase as tb

	with tb.testSetup():
		fl = Runner()

		fl.go()

