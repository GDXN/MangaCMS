
import feedparser
import webFunctions
import bs4
import re

import urllib.parse
import urllib.error
import time
import dateutil.parser
import runStatus
import settings
import datetime

import ScrapePlugins.RetreivalDbBase
import nameTools as nt

class MkFeedLoader(ScrapePlugins.RetreivalDbBase.ScraperDbBase):


	wg = webFunctions.WebGetRobust(creds=[("http://manga.madokami.com", settings.mkSettings["login"], settings.mkSettings["passWd"])])
	loggerPath = "Main.Mk.Fl"
	pluginName = "Manga.Madokami Link Retreiver"
	tableKey = "mk"
	dbName = settings.dbName


	urlBase = "http://manga.madokami.com/Manga"


	def checkLogin(self):
		pass

	def closeDB(self):
		self.log.info( "Closing DB...",)
		self.conn.close()
		self.log.info( "done")

	def getItemsFromContainer(self, dirName, dirUrl):

		# Skip the needs sorting directory.
		if dirName == 'Needs sorting':
			return [], []

		self.log.info("Original name - %s", dirName)

		bracketStripRe = re.compile(r"(\[.*?\])")
		dirName = bracketStripRe.sub(" ", dirName)
		while dirName.find("  ")+1:
			dirName = dirName.replace("  ", " ")

		dirName = nt.getCanonicalMangaUpdatesName(dirName)

		self.log.info("Canonical name - %s", dirName)
		self.log.info("Fetching items for directory '%s'", dirName)

		self.log.info("Using URL '%s'", dirUrl)
		try:
			itemPage = self.wg.getpage(dirUrl)
		except urllib.error.URLError:
			self.log.error("Could not fetch page '%s'", dirUrl)
			return [], []

		soup = bs4.BeautifulSoup(itemPage)

		itemRet = []
		dirRet  = []

		for row in soup.find_all("tr"):
			if "class" in row.attrs and row["class"] == ["path"]:
				newDirName = row.a.get_text().strip()
				dirUrl = urllib.parse.urljoin(dirUrl, row.a["href"])
				newDir = (newDirName, dirUrl)
				dirRet.append(newDir)
			elif "data-ext" in row.attrs:
				item = {}
				dlUrl = urllib.parse.urljoin(dirUrl, row.a["href"])
				item["date"]     = time.time()
				item["dlName"]   = row.a.get_text().strip()
				item["dlLink"]   = dlUrl
				item["baseName"] = dirName

				itemRet.append(item)

			else:
				print('"class" in row', "class" in row.attrs)
				print('row.attrs', row.attrs)
				raise ValueError("wat?")

		return dirRet, itemRet


	def getMainItems(self):
		# for item in items:
		# 	self.log.info( item)
		#

		self.log.info( "Loading Madokami Main Feed")

		items = []


		seriesPages, items = self.getItemsFromContainer("UNKNOWN", self.urlBase)

		while len(seriesPages):
			folderName, folderUrl = seriesPages.pop()

			newDirs, newItems = self.getItemsFromContainer(folderName, folderUrl)

			for newDir in newDirs:
				seriesPages.append(newDir)

			for newItem in newItems:
				items.append(newItem)

			if not runStatus.run:
				self.log.info("Breaking due to exit flag being set")
				return items
		return items




	def processLinksIntoDB(self, linksDicts, isPicked=False):

		self.log.info( "Inserting...",)
		newItems = 0
		for link in linksDicts:
			if link is None:
				print("linksDicts", linksDicts)
				print("WAT")

			rows = self.getRowsByValue(originName  = link["dlName"])    #We only look at filenames to determine uniqueness,
			if not rows:
				newItems += 1


				# Patch series name.
				seriesName = nt.getCanonicalMangaUpdatesName(link["baseName"])

				self.insertIntoDb(retreivalTime = link["date"],
									sourceUrl   = link["dlLink"],
									originName  = link["dlName"],
									dlState     = 0,
									seriesName  = seriesName,
									flags       = '')
				# Flags has to be an empty string, because the DB is annoying.
				# TL;DR, comparing with LIKE in a column that has NULLs in it is somewhat broken.


				self.log.info("New item: %s", (link["date"], link["dlLink"], link["baseName"], link["dlName"]))

			elif len(rows) > 1:
				self.log.warning("Have more then one item for filename! Wat?")
				self.log.warning("Info dict for file:")
				self.log.warning("'%s'", link)
				self.log.warning("Found rows:")
				self.log.warning("'%s'", rows)
			elif len(rows) == 1:
				row = rows.pop()
				if row["sourceUrl"] != link["dlLink"]:
					self.log.info("File has been moved!")
					self.log.info("File: '%s'", link)
					self.updateDbEntryById(row["dbId"], sourceUrl = link["dlLink"])

			else:
				row = row.pop()


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


