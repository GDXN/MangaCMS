
import runStatus
runStatus.preloadDicts = False


import webFunctions

import urllib.parse
import time
import calendar
import dateutil.parser
import settings

import ScrapePlugins.LoaderBase

# Only downlad items in language specified.
# Set to None to disable filtering (e.g. fetch ALL THE FILES).
DOWNLOAD_ONLY_LANGUAGE = "English"

class FeedLoader(ScrapePlugins.LoaderBase.LoaderBase):



	loggerPath = "Main.Manga.Ze.Fl"
	pluginName = "Comic-Zenon Magazine Link Retreiver"
	tableKey = "ze"
	dbName = settings.DATABASE_DB_NAME
	tableName = "MangaItems"

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")


	urlBase    = "http://www.manga-audition.com/comic-zenon/"




	def getSeriesPages(self):

		self.log.info( "Loading ComicZenon Items")

		ret = []

		soup = self.wg.getSoup(self.urlBase)

		main_chunk = soup.find_all("div", class_='ZenonComics')
		for chunk in main_chunk:
			for url_tag in chunk.find_all("a"):
				url = url_tag['href']
				if url.startswith("#"):
					continue
				if not url.startswith("http://comic.manga-audition.com"):
					ret.append(url)

		return ret

	def getChaptersFromSeriesPage(self, soup):


		items = []
		for row in soup.find_all("img", class_='ReadBtn'):

			item = {}
			item["sourceUrl"]  = row.parent['href']
			item['retreivalTime'] = time.time()

			items.append(item)

		return items

	def getChapterLinksFromSeriesPage(self, seriesUrl):
		ret = []
		soup = self.wg.getSoup(seriesUrl)


		ret = self.getChaptersFromSeriesPage(soup)
		self.log.info("Found %s items on page '%s'", len(ret), seriesUrl)

		return ret

	def getFeed(self):
		toScan = self.getSeriesPages()

		ret = []

		for url in toScan:
			items = self.getChapterLinksFromSeriesPage(url)
			for item in items:
				if item in ret:
					raise ValueError("Duplicate items in ret?")
				ret.append(item)
		return ret


if __name__ == '__main__':
	import utilities.testBase as tb

	with tb.testSetup():
		fl = FeedLoader()
		# fl.go(historical=True)
		fl.go()
		# fl.getChapterLinksFromSeriesPage('http://www.manga-audition.com/?p=5762')
		# fl.getSeriesUrls()

		# fl.getAllItems()

