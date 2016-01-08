
import runStatus
runStatus.preloadDicts = False


import webFunctions

import urllib.parse
import time
import calendar
import dateutil.parser
import settings

import ScrapePlugins.RetreivalDbBase

# Only downlad items in language specified.
# Set to None to disable filtering (e.g. fetch ALL THE FILES).
DOWNLOAD_ONLY_LANGUAGE = "English"

class FeedLoader(ScrapePlugins.RetreivalDbBase.ScraperDbBase):



	loggerPath = "Main.Manga.Mbx.Fl"
	pluginName = "MangaBox Link Retreiver"
	tableKey = "mbx"
	dbName = settings.DATABASE_DB_NAME
	tableName = "MangaItems"

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")


	urlBase    = "https://www.mangabox.me/reader/en/"


	def closeDB(self):
		self.log.info( "Closing DB...",)
		self.conn.close()
		self.log.info( "done")


	def getSeriesPages(self):

		self.log.info( "Loading ComicZenon Items")

		ret = []

		soup = self.wg.getSoup(self.urlBase)

		main_chunk = soup.find_all("article", class_='item_manga')
		for chunk in main_chunk:
			for url_tag in chunk.find_all("a", class_='bt_blue'):
				url = url_tag['href']

				if "latest" in url_tag.get_text().lower():
					print(url)
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

	def getAllItems(self):
		toScan = self.getSeriesPages()

		ret = []

		for url in toScan:
			items = self.getChapterLinksFromSeriesPage(url)
			for item in items:
				if item in ret:
					raise ValueError("Duplicate items in ret?")
				ret.append(item)
		return ret


	def go(self):

		# if not self.wg.stepThroughCloudFlare(self.urlBase, 'Manga from COMIC-ZENON'):
		# 	raise ValueError("Could not access site due to cloudflare protection.")

		self.resetStuckItems()
		self.log.info("Getting feed items")

		feedItems = self.getAllItems()
		self.log.info("Processing feed Items")

		# self.processLinksIntoDB(feedItems)
		# self.log.info("Complete")


if __name__ == '__main__':
	import utilities.testBase as tb

	with tb.testSetup(startObservers=False):
		fl = FeedLoader()
		# fl.go(historical=True)

		fl.getSeriesPages()
		# fl.go()

		# fl.getChapterLinksFromSeriesPage('http://www.manga-audition.com/?p=5762')
		# fl.getSeriesUrls()

		# fl.getAllItems()

