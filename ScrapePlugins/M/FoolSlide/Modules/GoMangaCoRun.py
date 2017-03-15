

import runStatus
import ScrapePlugins.M.FoolSlide.FoolSlideDownloadBase
import ScrapePlugins.M.FoolSlide.FoolSlideFetchBase
import ScrapePlugins.RetreivalBase
import ScrapePlugins.RetreivalDbBase
import ScrapePlugins.RunBase
import settings
import time
import webFunctions


class ContentLoader(ScrapePlugins.M.FoolSlide.FoolSlideDownloadBase.FoolContentLoader):




	loggerPath = "Main.Manga.GoMCo.Cl"
	tableKey = "gomco"
	pluginName = "GoManga.co Scans Content Retreiver"
	dbName = settings.DATABASE_DB_NAME
	tableName = "MangaItems"
	groupName = "GoManga.co"

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	retreivalThreads = 1

	contentSelector = ('article', 'content')


class FeedLoader(ScrapePlugins.M.FoolSlide.FoolSlideFetchBase.FoolFeedLoader):



	loggerPath = "Main.Manga.GoMCo.Fl"
	pluginName = "GoManga.co Scans Link Retreiver"
	tableKey = "gomco"
	dbName = settings.DATABASE_DB_NAME

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	tableName = "MangaItems"

	urlBase = "http://gomanga.co/reader/"
	feedUrl = urlBase+"latest/{num}/"




class Runner(ScrapePlugins.RunBase.ScraperBase):
	loggerPath = "Main.Manga.GoMCo.Run"

	pluginName = "GoMangaCoLoader"


	def _go(self):

		self.log.info("Checking GoManga.co feeds for updates")
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

		# cl = ContentLoader()
		# ret = cl.getImageUrls("http://gomanga.co/reader/read/hajimete_no_gal/en/0/13/")
		# print(ret)
		# ret = cl.getImageUrls("http://reader.roseliascans.com/read/futari_ecchi/en/24/225/")
		# print(ret)
		# ret = cl.getImageUrls("http://reader.s2smanga.com/read/dimension_w/en/4/31/5/page/1")
		# print(ret)

