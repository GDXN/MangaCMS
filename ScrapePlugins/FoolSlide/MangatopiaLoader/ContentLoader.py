
import webFunctions
import settings

import ScrapePlugins.RetreivalBase

import ScrapePlugins.FoolSlide.FoolSlideDownloadBase

class ContentLoader(ScrapePlugins.FoolSlide.FoolSlideDownloadBase.FoolContentLoader):




	loggerPath = "Main.MngTop.Cl"
	pluginName = "Mangatopia Content Retreiver"
	tableKey = "mp"
	dbName = settings.DATABASE_DB_NAME
	tableName = "MangaItems"
	groupName = "Mangatopia"

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	retreivalThreads = 1

	contentSelector = ('article', 'content')

if __name__ == '__main__':
	import utilities.testBase as tb

	with tb.testSetup():
		fl = ContentLoader()
		# fl.getImageUrls('http://mangatopia.net/slide/read/iron_knight/en-us/0/3/')
		fl.go()
