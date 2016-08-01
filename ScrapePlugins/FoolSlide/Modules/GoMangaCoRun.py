

import runStatus
import ScrapePlugins.FoolSlide.FoolSlideDownloadBase
import ScrapePlugins.FoolSlide.FoolSlideFetchBase
import ScrapePlugins.RetreivalBase
import ScrapePlugins.RetreivalDbBase
import ScrapePlugins.RunBase
import settings
import time
import webFunctions


class ContentLoader(ScrapePlugins.FoolSlide.FoolSlideDownloadBase.FoolContentLoader):




	loggerPath = "Main.Manga.GoMCo.Cl"
	tableKey = "gomco"
	pluginName = "GoManga.co Scans Content Retreiver"
	dbName = settings.DATABASE_DB_NAME
	tableName = "MangaItems"
	groupName = "GoManga.co"

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	retreivalThreads = 1

	contentSelector = ('article', 'content')


class FeedLoader(ScrapePlugins.FoolSlide.FoolSlideFetchBase.FoolFeedLoader):



	loggerPath = "Main.Manga.GoMCo.Fl"
	pluginName = "GoManga.co Scans Link Retreiver"
	tableKey = "gomco"
	dbName = settings.DATABASE_DB_NAME

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	tableName = "MangaItems"

	urlBase = "http://gomanga.co/reader/"
	feedUrl = urlBase+"reader/directory/{num}/"




class Runner(ScrapePlugins.RunBase.ScraperBase):
	loggerPath = "Main.Manga.GoMCo.Run"

	pluginName = "GoMangaCoLoader"


	def _go(self):

		self.log.info("Checking GoManga.co feeds for updates")
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

