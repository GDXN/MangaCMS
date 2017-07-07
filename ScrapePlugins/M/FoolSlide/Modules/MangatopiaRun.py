
import runStatus
import ScrapePlugins.M.FoolSlide.FoolSlideDownloadBase
import ScrapePlugins.M.FoolSlide.FoolSlideFetchBase


import ScrapePlugins.RunBase
import settings
import time
import webFunctions

class FeedLoader(ScrapePlugins.M.FoolSlide.FoolSlideFetchBase.FoolFeedLoader):



	loggerPath = "Main.Manga.MngTop.Cl"
	pluginName = "Mangatopia Content Retreiver"
	tableKey = "mp"
	dbName = settings.DATABASE_DB_NAME
	tableName = "MangaItems"
	groupName = "Mangatopia"

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")


	urlBase = "http://mangatopia.net/slide/"
	feedUrl = urlBase+"latest/{num}/"


	def filterItem(self, item):
		if "/es/" in item['sourceUrl']:
			return False

		if "[EN]" in item['seriesName']:
			item['seriesName'] = item['seriesName'].replace("[EN]", "").strip()

		return item


class ContentLoader(ScrapePlugins.M.FoolSlide.FoolSlideDownloadBase.FoolContentLoader):




	loggerPath = "Main.Manga.MngTop.Cl"
	pluginName = "Mangatopia Content Retreiver"
	tableKey = "mp"
	dbName = settings.DATABASE_DB_NAME
	tableName = "MangaItems"
	groupName = "Mangatopia"

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	retreivalThreads = 1

	contentSelector = ('article', 'content')



class Runner(ScrapePlugins.RunBase.ScraperBase):
	loggerPath = "Main.Manga.MngTop.Run"

	pluginName = "MangatopiaLoader"


	sourceName = "Mangatopia"

	feedLoader = FeedLoader
	contentLoader = ContentLoader


if __name__ == '__main__':
	import utilities.testBase as tb

	with tb.testSetup():
		fl = Runner()

		fl.go()

