
import webFunctions

import settings
import ScrapePlugins.RetreivalDbBase

import ScrapePlugins.FoolSlide.FoolSlideFetchBase

class FeedLoader(ScrapePlugins.FoolSlide.FoolSlideFetchBase.FoolFeedLoader):



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


if __name__ == '__main__':
	import utilities.testBase as tb

	with tb.testSetup():
		fl = FeedLoader()
		# for item in fl.getAllItems():
		# 	print(item)
		fl.go()
