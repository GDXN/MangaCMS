
import webFunctions
import settings
import ScrapePlugins.RetreivalBase
import ScrapePlugins.FoolSlide.FoolSlideDownloadBase

class ContentLoader(ScrapePlugins.FoolSlide.FoolSlideDownloadBase.FoolContentLoader):



	loggerPath = "Main.Manga.S2.Cl"
	pluginName = "S2 Scans Content Retreiver"
	tableKey = "s2"
	dbName = settings.DATABASE_DB_NAME
	tableName = "MangaItems"
	groupName = "S2Scans"

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	retreivalThreads = 2

	contentSelector = ('article', 'content')


if __name__ == '__main__':
	import utilities.testBase as tb

	with tb.testSetup(startObservers=True):
		fl = ContentLoader()

		fl.go()
