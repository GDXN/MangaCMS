
import webFunctions
import bs4
import re

import urllib.parse
import time
import dateutil.parser
import runStatus
import settings
import datetime

import ScrapePlugins.SeriesRetreivalDbBase
import nameTools as nt


DOWNLOAD_ONLY_LANGUAGE = "English"

class BtSeriesLoader(ScrapePlugins.SeriesRetreivalDbBase.SeriesScraperDbBase):



	loggerPath      = "Main.BtS.Sl"
	pluginName      = "Batoto Series Link Retreiver"
	tableKey        = "bt"
	dbName          = settings.DATABASE_DB_NAME

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	tableName       = "MangaItems"

	urlBase         = "http://www.bato.to/"

	feedUrl         = "http://www.bato.to/?p=%d"
	seriesTableName = "batotoSeries"

	listTableName   = "MangaSeries"

	wantedIds       = set()

	def extractSeriesDef(self, inTr):
		isSeries = inTr.find("td", colspan=5)
		if not isSeries:
			return None

		seriesName = isSeries.get_text().strip()
		seriesLink = isSeries.find("a", style="font-weight:bold;")
		seriesUrl  = seriesLink["href"]
		seriesId = seriesUrl.split("/")[-1]

		return seriesName, seriesId

	def checkInsertItem(self, item):
		seriesName, seriesId = item

		haveRows = self.getSeriesRowsByValue(seriesId=seriesId)
		if len(haveRows) == 1:
			item = haveRows.pop()

			# If item was last checked > 2 weeks ago, recheck it.
			if time.time() - 60*60*24*14 < item["lastUpdate"]:
				self.updateSeriesDbEntry(seriesId=item['seriesId'], dlState=0)

			return

		if len(haveRows) != 0:
			return				# We already have the series in the DB


		if not self.checkIfWantToFetchSeries(seriesName):
			self.log.info("Do not want to fetch content for series '%s'", seriesName)
			return
		self.log.info("Want to fetch content for series '%s'", seriesName)

		self.insertIntoSeriesDb(seriesId=seriesId,
								seriesName=seriesName,
								dlState=0,
								retreivalTime=time.time(),
								lastUpdate=0)


	def scanForSeries(self, rangeOverride=None, rangeOffset=None):
		# for item in items:
		# 	self.log.info( item)
		#


		self.log.info("Loading Monitored IDs from Batoto table")
		self.wantedIds = set(self.getBuListItemIds())
		self.log.info("Have %s items from Batoto lists to trigger on", len(self.wantedIds))


		self.log.info("Loading BT Main Feed")

		ret = []

		seriesPages = []

		if not rangeOverride:
			dayDelta = 1
		else:
			dayDelta = int(rangeOverride)
		if not rangeOffset:
			rangeOffset = 0


		for daysAgo in range(1, dayDelta+1):

			url = self.feedUrl % (daysAgo+rangeOffset)
			page = self.wg.getpage(url)
			soup = bs4.BeautifulSoup(page, "lxml")

			# Find the divs containing either new files, or the day a file was uploaded
			itemRow = soup.find_all("tr", class_=re.compile("row[01]"))

			for row in itemRow:

				item = self.extractSeriesDef(row)
				if item:
					self.checkInsertItem(item)

				if not runStatus.run:
					self.log.info( "Breaking due to exit flag being set")
					break

		return ret



	def go(self):

		self.log.info("Looking for new series to download")
		self.scanForSeries()

		self.log.info("Complete")



if __name__ == '__main__':
	import utilities.testBase as tb

	with tb.testSetup(startObservers=False):
		fl = BtSeriesLoader()

		fl.scanForSeries(rangeOverride=101)
		# fl.go()

