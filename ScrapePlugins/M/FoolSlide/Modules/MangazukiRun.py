


import runStatus
import ScrapePlugins.M.FoolSlide.FoolSlideDownloadBase
import ScrapePlugins.M.FoolSlide.FoolSlideFetchBase
import ScrapePlugins.RetreivalBase
import ScrapePlugins.RetreivalDbBase
import ScrapePlugins.RunBase
import settings
import settings
import time
import webFunctions

class FeedLoader(ScrapePlugins.M.FoolSlide.FoolSlideFetchBase.FoolFeedLoader):



	loggerPath = "Main.Manga.Mzk.Fl"
	pluginName = "Mangazuki Link Retreiver"
	tableKey = "mzk"
	dbName = settings.DATABASE_DB_NAME

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	tableName = "MangaItems"

	urlBase = "https://mangazuki.co/"
	feedUrl = urlBase+"directory/{num}/"

class ContentLoader(ScrapePlugins.M.FoolSlide.FoolSlideDownloadBase.FoolContentLoader):




	loggerPath = "Main.Manga.Mzk.Cl"
	pluginName = "Mangazuki Content Retreiver"
	tableKey = "mzk"
	dbName = settings.DATABASE_DB_NAME
	tableName = "MangaItems"
	groupName = "Mangazuki"

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	retreivalThreads = 1

	contentSelector = ('article', 'content')

class Runner(ScrapePlugins.RunBase.ScraperBase):
	loggerPath = "Main.Manga.Mzk.Run"

	pluginName = "MangazukiLoader"


	def _go(self):

		self.log.info("Checking Mangazuki feeds for updates")
		fl = FeedLoader()
		fl.go()
		fl.closeDB()

		time.sleep(3)
		#print "wat", cl

		if not runStatus.run:
			return

		cl = ContentLoader()

		if not runStatus.run:
			return

		todo = cl.retreiveTodoLinksFromDB()

		if not runStatus.run:
			return

		cl.processTodoLinks(todo)
		cl.closeDB()


if __name__ == '__main__':
	import utilities.testBase as tb

	with tb.testSetup():
		fl = Runner()

		fl.go()

