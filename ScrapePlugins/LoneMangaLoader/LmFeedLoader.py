
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

# Only downlad items in language specified.
# Set to None to disable filtering (e.g. fetch ALL THE FILES).
DOWNLOAD_ONLY_LANGUAGE = "English"

class LmFeedLoader(ScrapePlugins.RetreivalDbBase.ScraperDbBase):



	loggerPath = "Main.Manga.Lm.Fl"
	pluginName = "LoneManga Scans Link Retreiver"
	tableKey = "lm"
	dbName = settings.DATABASE_DB_NAME

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	tableName = "MangaItems"

	urlBase = "http://lonemanga.com/manga/"


	def closeDB(self):
		self.log.info( "Closing DB...",)
		self.conn.close()
		self.log.info( "done")




	def extractItemInfo(self, soup):

		ret = {}

		titleH = soup.find("h2", class_='kommiku-bread')

		# titleDiv = soup.find("h1", class_="ttl")
		ret["title"] = titleH.get_text().strip()

		return ret

	def getItemPages(self, url):
		self.log.info("Should get item for '%s'", url)
		soup = self.wg.getSoup(url)

		baseInfo = self.extractItemInfo(soup)

		ret = []

		for itemTd in soup.find_all("td", class_="series"):

			if not itemTd.a:
				continue

			linkTd, dateTd = itemTd.parent.find_all("td")


			item = {}

			link = linkTd.a

			url = link["href"]
			chapTitle = linkTd.get_text().strip()

			date = dateutil.parser.parse(dateTd.get_text().strip(), fuzzy=True)

			item["originName"] = "{series} - {file}".format(series=baseInfo["title"], file=chapTitle)
			item["sourceUrl"]  = url
			item["seriesName"] = baseInfo["title"]
			item["retreivalTime"]       = calendar.timegm(date.timetuple())

			ret.append(item)

		return ret



	def getSeriesUrls(self):
		ret = []

		soup = self.wg.getSoup(self.urlBase)
		itemTds = soup.find_all("td", class_='series')


		for td in itemTds:
			if td.a:
				link = td.a["href"]
				if self.urlBase in link:
					ret.append(link)

		print("Series URLs")

		return ret


	def getAllItems(self):
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


