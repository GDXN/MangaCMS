

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

import settings

import ScrapePlugins.RetreivalDbBase

class FeedLoader(ScrapePlugins.RetreivalDbBase.ScraperDbBase):



	loggerPath = "Main.Manga.Wr.Fl"
	pluginName = "Webtoons Reader Scans Link Retreiver"
	tableKey = "wr"
	dbName = settings.DATABASE_DB_NAME

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	tableName = "MangaItems"

	urlBase    = "http://www.webtoonsreader.com/"
	seriesBase = "http://www.webtoonsreader.com/comic-listing/"


	def closeDB(self):
		self.log.info( "Closing DB...",)
		self.conn.close()
		self.log.info( "done")




	def extractItemInfo(self, soup):

		ret = {}
		main = soup.find('div', class_='comic')

		ret["title"] = main.h1.get_text().strip()
		if not ret["title"]:
			ret["title"] = main.p.get_text().strip()

		return ret

	def getItemPages(self, pageUrl):
		self.log.info("Should get item for '%s'", pageUrl)

		ret = []

		soup = self.wg.getSoup(pageUrl)
		baseInfo = self.extractItemInfo(soup)

		chapDiv = soup.find('div', class_='comicchapters')

		for chapItem in chapDiv.find_all("li"):
			if not chapItem.p:
				continue
			if not chapItem.a:
				continue
			# Upload date is a <p> tag /inside/ the link tag.
			# As such, extract it, decompose it, and move on.
			ulDate = chapItem.p.get_text().strip()
			chapItem.p.decompose()

			chapTitle = chapItem.get_text().strip()

			date = dateutil.parser.parse(ulDate, fuzzy=True)

			item = {}

			url = chapItem.a["href"]
			url = urllib.parse.urljoin(self.urlBase, url)

			item["originName"]    = "{series} - {file}".format(series=baseInfo["title"], file=chapTitle)
			item["sourceUrl"]     = url
			item["seriesName"]    = baseInfo["title"]
			item["retreivalTime"] = calendar.timegm(date.timetuple())
			# print(item)
			if not item in ret:
				ret.append(item)

		self.log.info("Found %s chapters for series '%s'", len(ret), baseInfo["title"])
		return ret



	def getSeriesUrls(self):
		ret = set()

		soup = self.wg.getSoup(self.seriesBase)
		itemDiv = soup.find('div', class_='mng_lst')

		items = itemDiv.find_all("li")


		for item in items:
			if not item.a:
				continue

			ret.add(item.a['href'])

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
	# items = fl.getItemPages('http://www.webtoonsreader.com/black-haze/')
	# items = fl.getItemPages('http://www.webtoonsreader.com/Yokokuhan/')
	# print("Items")
	# for item in items:
	# 	print("	", item)

