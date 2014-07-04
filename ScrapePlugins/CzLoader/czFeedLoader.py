
import feedparser
import webFunctions
import bs4
import re

import urllib.parse
import time
import dateutil.parser
import runStatus
import settings
import datetime
import calendar

import ScrapePlugins.RetreivalDbBase
import nameTools as nt

class CzFeedLoader(ScrapePlugins.RetreivalDbBase.ScraperDbBase):



	wg = webFunctions.WebGetRobust()
	loggerPath = "Main.Cz.Fl"
	pluginName = "Crazy's Manga Link Retreiver"
	tableKey = "cz"
	dbName = settings.dbName


	urlBase = "http://crazytje.be/"

	feedUrl = "http://crazytje.be/Scanlation"


	# No login functionality
	def checkLogin(self):
		pass

	def closeDB(self):
		self.log.info( "Closing DB...",)
		self.conn.close()
		self.log.info( "done")






	def getItemsForSeries(self, seriesPageUrl):

		soup = self.wg.getpage(seriesPageUrl, soup=True)

		table = soup.find("table", id="tablesorter")

		if not table:
			self.log.warning("Manga Page has no content? WHRY YOU DO DIS CRAZY?")
			return []


		ret = []

		series = soup.find("td", class_="serie_details")
		seriesTitle = series.div.div.get_text().strip()


		rows = table.tbody.find_all("tr")
		for row in rows:
			updateDateStr = row.find("div", class_=re.compile("(old|new)")).get_text()
			titleStr = row.find("div", class_="description2").get_text()

			# For strings like "n Days Ago", split out the "n", convert it to an int, and take the
			# time-delta so we know what actual date it refers to.
			if "Days Ago" in updateDateStr:
				daysAgo = updateDateStr.strip().split()[0]
				daysAgo = int(daysAgo)
				updateDate = datetime.datetime.today() - datetime.timedelta(daysAgo)
			elif "Hours Ago" in updateDateStr:
				hoursAgo = updateDateStr.strip().split()[0]
				hoursAgo = int(hoursAgo)
				updateDate = datetime.datetime.today() - datetime.timedelta(0, hoursAgo*60*60)
			elif "Minutes Ago" in updateDateStr:
				minutesAgo = updateDateStr.strip().split()[0]
				minutesAgo = int(minutesAgo)
				updateDate = datetime.datetime.today() - datetime.timedelta(0, minutesAgo*60)
			elif "Seconds Ago" in updateDateStr:
				secondsAgo = updateDateStr.strip().split()[0]
				secondsAgo = int(secondsAgo)
				updateDate = datetime.datetime.today() - datetime.timedelta(0, secondsAgo)
			else:
				updateDate = dateutil.parser.parse(updateDateStr, fuzzy=True)

			# Drop any precision higher then the day, since the matching is kind of fuzzy
			# (e.g. "three hours ago" from datetime.now() changes since the minutes are included)
			updateDate = updateDate.date()
			updateDate = datetime.datetime.combine(updateDate, datetime.time(0, 0))

			# the "#" character is *explicitly* disallowed within URLs. Therefore, we can
			# use it to split on to recover both the seriesPage, and the fileName in the retreival stage
			link = seriesPageUrl+"#"+titleStr

			item = {}
			item["date"]     = calendar.timegm(updateDate.utctimetuple())
			item["dlLink"]   = link
			item["dlName"]   = titleStr
			item["baseName"] = seriesTitle

			ret.append(item)


		return ret


	def getMainItems(self, onlyRecent=True):
		# for item in items:
		# 	self.log.info( item)
		#
		self.log.info( "Loading SK Main Feed")

		ret = []

		soup = self.wg.getpage(self.feedUrl, soup=True)

		content = soup.find("div", class_="serie_list")
		links = content.find_all("div")

		for page in links:
			if page.find("a") and ("Ago]" in page.get_text() or not onlyRecent):

				ret.extend(self.getItemsForSeries(page.a["href"]))

		return ret


	def processLinksIntoDB(self, linksDicts, isPicked=False):

		self.log.info( "Inserting...",)
		newItems = 0

		flagStr = ""
		if isPicked:
			flagStr = "picked"

		for link in linksDicts:
			if link is None:
				print("linksDicts", linksDicts)
				print("WAT")

			row = self.getRowByValue(sourceUrl=link["dlLink"])
			if not row:
				newItems += 1
				# Flags has to be an empty string, because the DB is annoying.
				#
				# TL;DR, comparing with LIKE in a column that has NULLs in it is somewhat broken.
				#

				seriesName = nt.getCanonicalMangaUpdatesName(link["baseName"])

				self.insertIntoDb(retreivalTime = link["date"],
									sourceUrl   = link["dlLink"],
									originName  = link["dlName"],
									dlState     = 0,
									seriesName  = seriesName,
									flags       = flagStr)


				self.log.info("New item: %s", (link["date"], link["dlLink"], link["baseName"], link["dlName"]))

			if row and row["retreivalTime"] < link["date"]:

				# I cannot decide if I think it's safe to assume that any updated item will have a new filename. For the moment,
				# I'm not redownloading changed files, but that could change. We'll see.

				# self.updateDbEntry(link["dlLink"],
				# 					retreivalTime = link["date"],
				# 					originName  = link["dlName"],
				# 					dlState     = 0,
				# 					seriesName  = link["baseName"],
				# 					flags       = flagStr)

				self.log.warning("Item has changed?: %s", (link["date"], link["dlLink"], link["baseName"], link["dlName"]))

			else:

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


