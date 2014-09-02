
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



class CxFeedLoader(ScrapePlugins.RetreivalDbBase.ScraperDbBase):



	loggerPath = "Main.Cx.Fl"
	pluginName = "CXC Scans Link Retreiver"
	tableKey = "cx"
	dbName = settings.dbName

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	tableName = "MangaItems"

	urlBase = "http://www.cxcscans.com/"

	feedUrl = "http://manga.cxcscans.com/directory/"


	def closeDB(self):
		self.log.info( "Closing DB...",)
		self.conn.close()
		self.log.info( "done")


	def checkMatureAgree(self, page, url):
		if "This series contains mature contents" in page:
			self.log.info("Need to step through mature agreement page.")
			page = self.wg.getpage(url, postData={"adult" : "true"})

		return page

	def getItemPages(self, info):
		url, series = info

		# print("Should get item for ", url)
		page = self.wg.getpage(url)
		page = self.checkMatureAgree(page, url)

		soup = bs4.BeautifulSoup(page)

		series = soup.find("h1", class_="title")
		container = soup.find("div", class_="list")

		seriesName = series.get_text().strip()
		segmentDivs = container.find_all("div", class_="group", recursive=False)

		ret = []

		for segment in segmentDivs:
			chaps = segment.find_all("div", class_="element")
			for chap in chaps:
				dlLink = chap.find("div", class_="icon_wrapper").a["href"]
				dlTitle = chap.find("div", class_="title").get_text()

				dlTitle = dlTitle.replace(":", " -")  # Can't have colons in filenames
				# print("dlLink", dlLink, dlTitle)

				item = {}


				chapDate = chap.find("div", class_="meta_r")
				datestr = list(chapDate)[-1]
				datestr.strip(", ")

				date = dateutil.parser.parse(datestr, fuzzy=True)

				item["originName"] = "{series} - {file}".format(series=seriesName, file=dlTitle)
				item["sourceUrl"]  = dlLink
				item["seriesName"] = seriesName
				item["date"]       = time.mktime(date.timetuple())

				# print("Item", item)
				ret.append(item)

		return ret



	def getSeriesUrls(self):
		ret = []
		page = self.wg.getpage(self.feedUrl)
		soup = bs4.BeautifulSoup(page)
		divs = soup.find_all("div", class_="group")
		for div in divs:
			# First div in the group div is the title. Yes, this is probably brittle
			url = div.div.a["href"]
			text = div.div.get_text()
			ret.append((url, text))

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


