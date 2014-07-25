
import webFunctions
import bs4
import re

import urllib.parse
import time
import dateutil.parser
import runStatus
import settings
import datetime
import nameTools as nt

import ScrapePlugins.RetreivalDbBase


class MbFeedLoader(ScrapePlugins.RetreivalDbBase.ScraperDbBase):



	wg = webFunctions.WebGetRobust()
	loggerPath = "Main.Mb.Fl"
	pluginName = "MangaBaby Link Retreiver"
	tableKey = "mb"
	dbName = settings.dbName

	tableName = "MangaItems"
	urlBase = "http://www.mangababy.com/"


	def checkLogin(self):
		return True

	def closeDB(self):
		self.log.info( "Closing DB...",)
		self.conn.close()
		self.log.info( "done")



	def getItemsFromContainer(self, segmentSoup):




		# chName, seriesName, size, view = segmentSoupItems
		title = segmentSoup.find("a", class_="mtit")
		if not title:
			return []

		title = title.get_text()
		# print("Title = ", title)

		ret = []

		for item in segmentSoup.find_all("a", class_="btit"):

			href = item["href"]
			href = href.replace("/manga/", "/download/")
			# Links are to the reader page. Tweak the URL so they go to the download page.

			url = urllib.parse.urljoin(self.urlBase, href)
			# print("item", url)
			# print("date", dateutil.parser.parse(item.next_sibling.next_sibling.get_text()))

			ch = item.get_text()
			ch = ch.replace("Ch.", "c")
			chName = "{series} - {chapter}".format(series=title, chapter=ch)
			# print("Chap = ", chName)

			entry = {}

			addDate = dateutil.parser.parse(item.next_sibling.next_sibling.get_text())

			# since we don't have the year, if any items were uploaded in previous years, they can show up as
			# being in the future. Therefore, for any items that have timestamps > current, we
			# deincrement them in year steps untill they are in the past
			# The +12 hours is a fudge-factor since I don't know the source time zone.
			# Possibly increase it to 24 in the
			while addDate > datetime.datetime.now() + datetime.timedelta(hours=12):
				addDate = addDate - datetime.timedelta(days=365)

			entry["date"] = time.mktime(addDate.timetuple())
			entry["dlName"] = chName
			entry["dlLink"] =  url
			entry["baseName"] = nt.makeFilenameSafe(title)

			# print("entry", entry)

			ret.append(entry)
		return ret


	def getItems(self):
		# for item in items:
		# 	self.log.info( item)
		#

		self.log.info( "Loading MB Main Feed")

		ret = []

		url = self.urlBase
		page = self.wg.getpage(url)
		soup = bs4.BeautifulSoup(page)

		# Find the divs a series that changed recently
		seriesContainers = soup.find_all("div", class_="text")

		for div in seriesContainers:

			items = self.getItemsFromContainer(div)
			# item = self.getItemFromContainer(div, currentDate)
			# ret.append(item)

			for item in items:
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
				flagStr = ""
				if isPicked:
					flagStr = "picked"

				seriesName = nt.getCanonicalMangaUpdatesName(link["baseName"])

				self.insertIntoDb(retreivalTime = link["date"],
									sourceUrl   = link["dlLink"],
									originName  = link["dlName"],
									dlState     = 0,
									seriesName  = seriesName,
									flags       = flagStr)


				self.log.info("New item: %s", (link["date"], link["dlLink"], link["baseName"], link["dlName"]))


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

		feedItems = self.getItems()
		self.log.info("Processing %s feed Items", len(feedItems))

		self.processLinksIntoDB(feedItems)
		self.log.info("Complete")


