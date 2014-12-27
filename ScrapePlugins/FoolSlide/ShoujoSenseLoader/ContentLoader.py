
import webFunctions
import settings

import ScrapePlugins.RetreivalBase

import ScrapePlugins.FoolSlide.FoolSlideDownloadBase

class ContentLoader(ScrapePlugins.FoolSlide.FoolSlideDownloadBase.FoolContentLoader):


	loggerPath = "Main.Sj.Cl"
	pluginName = "Shoujo Sense Scans Content Retreiver"
	tableKey = "sj"
	dbName = settings.DATABASE_DB_NAME
	tableName = "MangaItems"
	groupName = "ShoujoSense"

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	retreivalThreads = 1

	contentSelector = ('article', 'content')

if __name__ == '__main__':
	import utilities.testBase as tb

	with tb.testSetup():
		fl = ContentLoader()

		fl.go()
