
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

class BtFeedLoader(ScrapePlugins.RetreivalDbBase.ScraperDbBase):



	loggerPath = "Main.Bt.Fl"
	pluginName = "Batoto Link Retreiver"
	tableKey = "bt"
	dbName = settings.dbName

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	tableName = "MangaItems"

	urlBase = "http://www.batoto.net/"

	feedUrl = "http://www.batoto.net/?p=%d"


	def closeDB(self):
		self.log.info( "Closing DB...",)
		self.conn.close()
		self.log.info( "done")



	def getItemFromContainer(self, row):

		cells = row.find_all("td")

		if len(cells) != 4 and len(cells) != 5:
			return None

		if len(cells) == 4:
			chapter, lang, dummy_scanlator, uploadDate = cells
		elif len(cells) == 5:
			dummy_blank, chapter, lang, dummy_scanlator, uploadDate = cells

		# Skip uploads in other languages
		if DOWNLOAD_ONLY_LANGUAGE and not DOWNLOAD_ONLY_LANGUAGE in str(lang):
			return None


		dateStr = uploadDate.get_text().strip()
		addDate = self.parseDateStr(dateStr)

		item = {}

		item["date"] = time.mktime(addDate.timetuple())
		item["dlLink"] = chapter.a["href"]

		return item

	def parseDateStr(self, inStr):

		# For strings like "n Days Ago", split out the "n", convert it to an int, and take the
		# time-delta so we know what actual date it refers to.

		# convert instances of "a minute ago" to "1 minute ago", for mins, hours, etc...
		inStr = inStr.strip()
		if inStr.lower().startswith("an"):
			inStr = "1"+inStr[2:]

		if inStr.lower().startswith("a"):
			inStr = "1"+inStr[1:]

		if "just now" in inStr:
			updateDate = datetime.datetime.now()
		elif "months ago" in inStr or "month ago" in inStr:
			monthsAgo = inStr.split()[0]
			monthsAgo = int(monthsAgo)
			updateDate = datetime.datetime.now() - datetime.timedelta(monthsAgo*7)
		elif "weeks ago" in inStr or "week ago" in inStr:
			weeksAgo = inStr.split()[0]
			weeksAgo = int(weeksAgo)
			updateDate = datetime.datetime.now() - datetime.timedelta(weeksAgo*7)
		elif "days ago" in inStr or "day ago" in inStr:
			daysAgo = inStr.split()[0]
			daysAgo = int(daysAgo)
			updateDate = datetime.datetime.now() - datetime.timedelta(daysAgo)
		elif "hours ago" in inStr or "hour ago" in inStr:
			hoursAgo = inStr.split()[0]
			hoursAgo = int(hoursAgo)
			updateDate = datetime.datetime.now() - datetime.timedelta(0, hoursAgo*60*60)
		elif "minutes ago" in inStr or "minute ago" in inStr:
			minutesAgo = inStr.split()[0]
			minutesAgo = int(minutesAgo)
			updateDate = datetime.datetime.now() - datetime.timedelta(0, minutesAgo*60)
		elif "seconds ago" in inStr or "second ago" in inStr:
			secondsAgo = inStr.split()[0]
			secondsAgo = int(secondsAgo)
			updateDate = datetime.datetime.now() - datetime.timedelta(0, secondsAgo)
		else:
			# self.log.warning("Date parsing failed. Using fall-back parser")
			updateDate = dateutil.parser.parse(inStr, fuzzy=True)
			# self.log.warning("Failing string = '%s'", inStr)
			# self.log.warning("As parsed = '%s'", updateDate)

		return updateDate

	def getMainItems(self, rangeOverride=None, rangeOffset=None):
		# for item in items:
		# 	self.log.info( item)
		#

		self.log.info( "Loading BT Main Feed")

		ret = []

		seriesPages = []

		if not rangeOverride:
			dayDelta = 3
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

				item = self.getItemFromContainer(row)
				if item:
					ret.append(item)

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
				#
				self.insertIntoDb(retreivalTime = link["date"],
									sourceUrl   = link["dlLink"],
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


