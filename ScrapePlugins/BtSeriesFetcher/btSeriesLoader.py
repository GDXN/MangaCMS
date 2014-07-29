
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



	wg              = webFunctions.WebGetRobust()
	loggerPath      = "Main.BtS.Fl"
	pluginName      = "Batoto Series Link Retreiver"
	tableKey        = "bt"
	dbName          = settings.dbName

	tableName       = "MangaItems"

	urlBase         = "http://www.batoto.net/"

	feedUrl         = "http://www.batoto.net/?p=%d"
	seriesTableName = "batotoSeries"


	def extractSeriesDef(self, inTr):
		isSeries = inTr.find("td", colspan=5)
		if not isSeries:
			return None

		print("Series TD!")
		seriesName = isSeries.get_text().strip()
		seriesLink = isSeries.find("a", style="font-weight:bold;")
		seriesUrl  = seriesLink["href"]
		seriesId = seriesUrl.split("/")[-1]
		print("Name", seriesName, "url", seriesId)

		return seriesName, seriesId

	def checkInsertItem(self, item):
		seriesName, seriesId = item
		canonSeriesName = nt.getCanonicalMangaUpdatesName(seriesName)

		if canonSeriesName not in nt.dirNameProxy:
			return

		rating = nt.dirNameProxy[canonSeriesName]["rating"]
		rating = nt.ratingStrToInt(rating)
		if rating < 2:
			return

		haveRows = self.getSeriesRowsByValue(seriesId=seriesId)
		if len(haveRows) != 0:
			return				# We already have the series in the DB

		self.log.info("New series! '%s', '%s'", seriesName, seriesId)
		self.insertIntoSeriesDb(seriesId=seriesId,
								seriesName=seriesName,
								dlState=0,
								retreivalTime=time.time(),
								lastUpdate=0)


	def ScanForSeries(self, rangeOverride=None, rangeOffset=None):
		# for item in items:
		# 	self.log.info( item)
		#

		self.log.info( "Loading BT Main Feed")

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
			soup = bs4.BeautifulSoup(page)

			# Find the divs containing either new files, or the day a file was uploaded
			itemRow = soup.find_all("tr", class_=re.compile("row[01]"))

			for row in itemRow:

				item = self.extractSeriesDef(row)
				if item:
					self.checkInsertItem(item)
					print("Item", item)
				if not runStatus.run:
					self.log.info( "Breaking due to exit flag being set")
					break

		return ret



	def go(self):

		self.log.info("Looking for new series to download")
		self.ScanForSeries()

		self.log.info("Complete")


