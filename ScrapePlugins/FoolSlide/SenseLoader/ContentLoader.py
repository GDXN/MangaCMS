
import webFunctions
import settings

import ScrapePlugins.RetreivalBase

import ScrapePlugins.FoolSlide.FoolSlideDownloadBase

class ContentLoader(ScrapePlugins.FoolSlide.FoolSlideDownloadBase.FoolContentLoader):


	loggerPath = "Main.Se.Cl"
	pluginName = "Sense Scans Content Retreiver"
	tableKey = "se"
	dbName = settings.DATABASE_DB_NAME
	tableName = "MangaItems"
	groupName = "SenseScans"

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	retreivalThreads = 1

	contentSelector = ('article', 'content')

if __name__ == '__main__':
	import utilities.testBase as tb

	with tb.testSetup():
		fl = ContentLoader()

		fl.go()
