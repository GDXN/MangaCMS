
import webFunctions
import bs4
import re

import urllib.parse
import time
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



	wg = webFunctions.WebGetRobust()
	loggerPath = "Main.Mc.Fl"
	pluginName = "MangaCow Link Retreiver"
	tableKey = "mc"
	dbName = settings.dbName

	tableName = "MangaItems"

	urlBase = "http://mngacow.com/"

	feedUrl = "http://mngacow.com/manga-list/"


	def closeDB(self):
		self.log.info( "Closing DB...",)
		self.conn.close()
		self.log.info( "done")




	def extractItemInfo(self, soup):

		ret = {}

		titleDiv = soup.find("h1", class_="ttl")
		ret["title"] = titleDiv.get_text()

		container = soup.find("div", class_="mng_ifo")
		infoDiv = container.find("div", class_="det")
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
				tags = text.split(",")
				tags = [tag.lower().strip().replace(" ", "-") for tag in tags]
				ret["tags"] = " ".join(tags)


		return ret

	def getItemPages(self, url):
		print("Should get item for ", url)
		page = self.wg.getpage(url)


		soup = bs4.BeautifulSoup(page)
		baseInfo = self.extractItemInfo(soup)

		ret = []
		for link in soup.find_all("a", class_="lst"):
			item = {}

			url = link["href"]
			chapTitle = link.find("b", class_="val")
			chapTitle = chapTitle.get_text()

			chapDate = link.find("b", class_="dte")

			date = dateutil.parser.parse(chapDate.get_text(), fuzzy=True)

			item["originName"] = "{series} - {file}".format(series=baseInfo["title"], file=chapTitle)
			item["sourceUrl"]  = url
			item["seriesName"] = baseInfo["title"]
			item["tags"]       = baseInfo["tags"]
			item["note"]       = baseInfo["note"]
			item["date"]       = time.mktime(date.timetuple())


			ret.append(item)

		return ret



	def getSeriesUrls(self):
		ret = []
		print("wat?")
		page = self.wg.getpage(self.feedUrl)
		soup = bs4.BeautifulSoup(page)
		divs = soup.find_all("div", class_="nde")
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




	def processLinksIntoDB(self, linksDicts, isPicked=False):

		self.log.info( "Inserting...",)
		newItems = 0
		for link in linksDicts:
			if link is None:
				print("linksDicts", linksDicts)
				print("WAT")

			row = self.getRowsByValue(sourceUrl=link["sourceUrl"])
			if not row:
				newItems += 1


				# Flags has to be an empty string, because the DB is annoying.
				#
				# TL;DR, comparing with LIKE in a column that has NULLs in it is somewhat broken.
				#
				self.insertIntoDb(originName      = link["originName"],
									sourceUrl     = link["sourceUrl"],
									seriesName    = link["seriesName"],
									tags          = link["tags"],
									note          = link["note"],
									retreivalTime = link["date"],
									dlState     = 0,
									flags       = '')



				self.log.info("New item: %s, %s", link["date"], link["sourceUrl"])


			else:
				row = row.pop()
				if isPicked and not "picked" in row["flags"]:  # Set the picked flag if it's not already there, and we have the item already
					self.updateDbEntry(link["dlLink"], flags=" ".join([row["flags"], "picked"]))


		self.log.info( "Done")
		self.log.info( "Committing...",)
		self.conn.commit()
		self.log.info( "Committed")

		return newItems


	def go(self):

		self.resetStuckItems()
		self.log.info("Getting feed items")

		feedItems = self.getAllItems()
		self.log.info("Processing feed Items")

		self.processLinksIntoDB(feedItems)
		self.log.info("Complete")


