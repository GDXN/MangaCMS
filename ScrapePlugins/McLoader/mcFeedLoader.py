
import webFunctions
import bs4
import re

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

class McFeedLoader(ScrapePlugins.RetreivalDbBase.ScraperDbBase):



	loggerPath = "Main.Manga.Mc.Fl"
	pluginName = "MangaCow Link Retreiver"
	tableKey = "mc"
	dbName = settings.DATABASE_DB_NAME

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	tableName = "MangaItems"

	urlBase = "http://mngcow.co/"

	feedUrl = "http://mngcow.co/manga-list/"


	def closeDB(self):
		self.log.info( "Closing DB...",)
		self.conn.close()
		self.log.info( "done")




	def extractItemInfo(self, soup):

		ret = {}
		container = soup.find("div", class_="mng_ifo")
		infoDiv = container.find("div", class_="det")

		titleDiv = infoDiv.find("h4")
		ret["title"] = titleDiv.get_text()

		items = infoDiv.find_all("p")

		ret["note"] = " ".join(items[0].strings)   # Messy hack to replace <br> tags with a ' ', rather then just removing them.

		# And clean out the non-breaking spaces
		ret["note"] = ret["note"].replace(chr(0xa0), ' ')

		for item in items:
			text = item.get_text().strip()
			if not ":" in text:
				continue

			what, text = text.split(":", 1)
			if what == "Category":
				tags = [tag_link.get_text() for tag_link in item.find_all("a")]

				tags = [tag.lower().strip().replace(" ", "-") for tag in tags]
				ret["tags"] = " ".join(tags)

		return ret

	def getItemPages(self, url):
		# print("Should get item for ", url)
		page = self.wg.getpage(url)


		soup = bs4.BeautifulSoup(page, "lxml")
		baseInfo = self.extractItemInfo(soup)

		ret = []
		for link in soup.find_all("a", class_="lst"):
			item = {}

			url = link["href"]
			chapTitle = link.find("b", class_="val")
			chapTitle = chapTitle.get_text()

			chapDate = link.find("b", class_="dte")

			date = dateutil.parser.parse(chapDate.get_text(), fuzzy=True)

			item["originName"]     = "{series} - {file}".format(series=baseInfo["title"], file=chapTitle)
			item["sourceUrl"]      = url
			item["seriesName"]     = baseInfo["title"]
			item["tags"]           = baseInfo["tags"]
			item["note"]           = baseInfo["note"]
			item["retreivalTime"]  = calendar.timegm(date.timetuple())


			ret.append(item)

		return ret



	def getSeriesUrls(self):
		ret = []
		print("wat?")
		page = self.wg.getpage(self.feedUrl)
		soup = bs4.BeautifulSoup(page, "lxml")
		divs = soup.find_all("div", class_="img_wrp")
		for div in divs:
			url = div.a["href"]
			ret.append(url)

		return ret

	def getAllItems(self):
		# for item in items:
		# 	self.log.info( item)
		#

		self.log.info( "Loading Mc Items")

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



if __name__ == "__main__":
	import utilities.testBase as tb

	with tb.testSetup(startObservers=False):

		run = McFeedLoader()
		run.go()


