


import ScrapePlugins.RunBase
import settings
import ScrapePlugins.RetreivalDbBase
import ScrapePlugins.M.FoolSlide.FoolSlideFetchBase
import ScrapePlugins.RetreivalBase
import ScrapePlugins.M.FoolSlide.FoolSlideDownloadBase

import time
import runStatus
import webFunctions

DB_KEY     = "cm"
LONG_NAME  = "Chibi Manga Scanlation"
SHORT_NAME = "CM"
GROUP_NAME = "ChibiMangaScanlation"

URL_BASE = "http://www.cmreader.info/"
READER_POSTFIX = "latest/{num}/"

class FeedLoader(ScrapePlugins.M.FoolSlide.FoolSlideFetchBase.FoolFeedLoader):



	loggerPath = "Main.Manga.%s.Fl" % SHORT_NAME
	pluginName = "%s Link Retreiver" % LONG_NAME
	tableKey = DB_KEY
	dbName = settings.DATABASE_DB_NAME

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	tableName = "MangaItems"

	urlBase = URL_BASE
	feedUrl = urlBase+READER_POSTFIX



class ContentLoader(ScrapePlugins.M.FoolSlide.FoolSlideDownloadBase.FoolContentLoader):




	loggerPath = "Main.Manga.%s.Cl" % SHORT_NAME
	pluginName = "%s Content Retreiver" % LONG_NAME
	tableKey = DB_KEY
	dbName = settings.DATABASE_DB_NAME
	tableName = "MangaItems"
	groupName = GROUP_NAME

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	retreivalThreads = 1

	contentSelector = ('article', 'content')

class Runner(ScrapePlugins.RunBase.ScraperBase):
	loggerPath = "Main.Manga.%s.Run" % SHORT_NAME

	pluginName = "%sLoader" % GROUP_NAME


	def _go(self):

		self.log.info("Checking %s feeds for updates" % LONG_NAME)
		fl = FeedLoader()
		fl.go()

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


if __name__ == '__main__':
	import utilities.testBase as tb

	with tb.testSetup():
		fl = Runner()

		fl.go()

