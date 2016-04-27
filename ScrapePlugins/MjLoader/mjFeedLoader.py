
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

class MjFeedLoader(ScrapePlugins.RetreivalDbBase.ScraperDbBase):



	loggerPath = "Main.Manga.Mj.Fl"
	pluginName = "MangaJoy Link Retreiver"
	tableKey = "mj"
	dbName = settings.DATABASE_DB_NAME

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	tableName = "MangaItems"

	urlBase = "http://mangajoy.com/"
	updateFeed = "http://manga-joy.com/latest-chapters/{pageNo}/"


	def closeDB(self):
		self.log.info( "Closing DB...",)
		self.conn.close()
		self.log.info( "done")


	def getItemsFromContainer(self, divSoup):
		# print("Div", divSoup)
		titleLink = divSoup.find("a", class_="ttl")
		items = divSoup.find_all("li")
		series = list(titleLink.children).pop(0).strip()

		dlItems = []
		for row in items:

			item = {}

			url = row.a["href"]
			chpName, ulDate = row.find_all("b")
			chpName = chpName.get_text().strip()
			ulDate = ulDate.get_text().strip()

			if ulDate == "Today":
				ulDate = datetime.datetime.now()
			else:
				ulDate = dateutil.parser.parse(ulDate, fuzzy=True)


			item["series"]   = series
			item["chapName"] = '{series} - {chapter}'.format(series=series, chapter=chpName)
			item["date"]     = calendar.timegm(ulDate.timetuple())
			item["dlLink"]   = url
			dlItems.append(item)
		return dlItems

	def getMainItems(self, rangeOverride=None, rangeOffset=None):
		# for item in items:
		# 	self.log.info( item)
		#

		self.log.info( "Loading Mj Main Feed")

		ret = []

		seriesPages = []

		if rangeOverride is None:
			dayDelta = 3
		else:
			dayDelta = int(rangeOverride)
		if not rangeOffset:
			rangeOffset = 0


		for daysAgo in range(1, dayDelta+1):

			url = self.updateFeed.format(pageNo=daysAgo+rangeOffset)
			page = self.wg.getpage(url)
			soup = bs4.BeautifulSoup(page, "lxml")

			# Find the divs containing either new files, or the day a file was uploaded
			mainDiv = soup.find("div", class_="mng_lts_chp")

			itemRows = mainDiv.find_all("div", class_="row")

			for row in itemRows:

				ret += self.getItemsFromContainer(row)
				if not runStatus.run:
					self.log.info( "Breaking due to exit flag being set")
					break

		return ret




	def processLinksIntoDB(self, linksDicts, isPicked=False):

		self.log.info( "Inserting...",)
		newItems = 0
		for link in linksDicts:
			if link is None:
				print("linksDicts", linksDicts)
				print("WAT")

			row = self.getRowsByValue(sourceUrl=link["dlLink"])
			if not row:
				newItems += 1


				# Flags has to be an empty string, because the DB is annoying.
				#
				# TL;DR, comparing with LIKE in a column that has NULLs in it is somewhat broken.
				self.insertIntoDb(retreivalTime = link["date"],
									sourceUrl   = link["dlLink"],
									originName  = link["chapName"],
									seriesName  = link["series"],
									dlState     = 0,
									flags       = '')


				self.log.info("New item: %s, %s", link["date"], link["dlLink"])


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

		feedItems = self.getMainItems()
		self.log.info("Processing feed Items")

		self.processLinksIntoDB(feedItems)
		self.log.info("Complete")

def history():
	run = MjFeedLoader()
	for x in range(150):
		links = run.getMainItems(rangeOverride=1, rangeOffset=x)
		run.processLinksIntoDB(links)



if __name__ == "__main__":
	import utilities.testBase as tb

	with tb.testSetup(startObservers=False):
		history()
		# run = MjFeedLoader()
		# run.go()



