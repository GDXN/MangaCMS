

import logSetup
import runStatus
if __name__ == "__main__":
	logSetup.initLogging()
	runStatus.preloadDicts = False


import webFunctions

import urllib.parse
import time
import calendar
import dateutil.parser
import runStatus
import settings
import datetime

import ScrapePlugins.RetreivalDbBase
import nameTools as nt

class FeedLoader(ScrapePlugins.RetreivalDbBase.ScraperDbBase):



	loggerPath = "Main.Manga.Ms.Fl"
	pluginName = "Mangastream.com Scans Link Retreiver"
	tableKey = "ms"
	dbName = settings.DATABASE_DB_NAME

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	tableName = "MangaItems"

	urlBase    = "http://mangastream.com/"
	seriesBase = "http://mangastream.com/manga"


	def closeDB(self):
		self.log.info( "Closing DB...",)
		self.conn.close()
		self.log.info( "done")




	def extractItemInfo(self, soup):

		ret = {}
		main = soup.find('div', class_='span8')

		ret["title"] = main.h1.get_text().strip()

		return ret

	def getItemPages(self, pageUrl):
		self.log.info("Should get item for '%s'", pageUrl)

		ret = []

		soup = self.wg.getSoup(pageUrl)
		baseInfo = self.extractItemInfo(soup)

		table = soup.find('table', class_='table-striped')

		for row in table.find_all("tr"):

			if not row.td:
				continue
			if not row.a:
				continue
			chapter, ulDate = row.find_all('td')

			chapTitle = chapter.get_text().strip()

			# Fix stupid chapter naming
			chapTitle = chapTitle.replace("Ep. ", "c")

			date = dateutil.parser.parse(ulDate.get_text().strip(), fuzzy=True)

			item = {}

			url = row.a["href"]
			url = urllib.parse.urljoin(self.urlBase, url)

			item["originName"]    = "{series} - {file}".format(series=baseInfo["title"], file=chapTitle)
			item["sourceUrl"]     = url
			item["seriesName"]    = baseInfo["title"]
			item["retreivalTime"] = calendar.timegm(date.timetuple())

			if not item in ret:
				ret.append(item)

		self.log.info("Found %s chapters for series '%s'", len(ret), baseInfo["title"])
		return ret



	def getSeriesUrls(self):
		ret = set()

		soup = self.wg.getSoup(self.seriesBase)
		table = soup.find('table', class_='table-striped')

		rows = table.find_all("tr")


		for row in rows:
			if not row.td:
				continue
			series, dummy_chapName = row.find_all('td')
			if not series.a:
				continue


			ret.add(series.a['href'])

		self.log.info("Found %s series", len(ret))

		return ret


	def getAllItems(self, historical=False):
		# for item in items:
		# 	self.log.info( item)
		#

		self.log.info( "Loading Red Hawk Items")

		ret = []

		seriesPages = self.getSeriesUrls()


		for item in seriesPages:

			itemList = self.getItemPages(item)
			for item in itemList:
				ret.append(item)

			if not runStatus.run:
				self.log.info( "Breaking due to exit flag being set")
				break
		self.log.info("Found %s total items", len(ret))
		return ret


	def go(self):

		self.resetStuckItems()
		self.log.info("Getting feed items")

		feedItems = self.getAllItems()
		self.log.info("Processing feed Items")

		self.processLinksIntoDB(feedItems)
		self.log.info("Complete")


if __name__ == '__main__':
	fl = FeedLoader()
	print("fl", fl)
	fl.go()
	# fl.getSeriesUrls()
	# items = fl.getItemPages('http://mangastream.com/manga/area_d')
	# print("Items")
	# for item in items:
	# 	print("	", item)

