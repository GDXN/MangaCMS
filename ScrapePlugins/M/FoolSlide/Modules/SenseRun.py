
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


	loggerPath = "Main.Manga.Se.Cl"
	pluginName = "Sense Scans Content Retreiver"
	tableKey = "se"
	dbName = settings.DATABASE_DB_NAME
	tableName = "MangaItems"
	groupName = "SenseScans"

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	retreivalThreads = 1

	contentSelector = ('article', 'content')


class FeedLoader(ScrapePlugins.M.FoolSlide.FoolSlideFetchBase.FoolFeedLoader):


	loggerPath = "Main.Manga.Se.Fl"
	pluginName = "Sense Scans Link Retreiver"
	tableKey = "se"
	dbName = settings.DATABASE_DB_NAME
	tableName = "MangaItems"


	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	urlBase = "http://reader.sensescans.com/"
	feedUrl = urlBase+"reader/list/{num}/"


class Runner(ScrapePlugins.RunBase.ScraperBase):
	loggerPath = "Main.Manga.Se.Run"

	pluginName = "SenseLoader"


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

