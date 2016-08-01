

import runStatus
import ScrapePlugins.FoolSlide.FoolSlideDownloadBase
import ScrapePlugins.FoolSlide.FoolSlideFetchBase
import ScrapePlugins.RetreivalBase
import ScrapePlugins.RetreivalDbBase
import ScrapePlugins.RunBase
import settings
import time
import webFunctions

class FeedLoader(ScrapePlugins.FoolSlide.FoolSlideFetchBase.FoolFeedLoader):


	loggerPath = "Main.Manga.Sj.Fl"
	pluginName = "Shoujo Sense Scans Link Retreiver"
	tableKey = "sj"
	dbName = settings.DATABASE_DB_NAME
	tableName = "MangaItems"


	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	urlBase = "http://reader.shoujosense.com/"
	feedUrl = urlBase+"reader/list/{num}/"

class ContentLoader(ScrapePlugins.FoolSlide.FoolSlideDownloadBase.FoolContentLoader):


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


	def _go(self):

		self.log.info("Checking Sense Scans feeds for updates")
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

