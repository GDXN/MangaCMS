
import webFunctions
import bs4
import re

import urllib.parse
import urllib.error
import time
import runStatus
import settings
import json
import ScrapePlugins.RetreivalDbBase
import ScrapePlugins.RunBase
import nameTools as nt
from concurrent.futures import ThreadPoolExecutor

MASK_PATHS = [
	'/Raws',
	'/Raws',
	'/Requests',
	'/READ.txt',
	'/Needs%20sorting',
	'/Admin%20cleanup',
	'/_Autouploads',
	'/Non-English',
]

HTTPS_CREDS = [
	("manga.madokami.com", settings.mkSettings["login"], settings.mkSettings["passWd"]),
	("http://manga.madokami.com", settings.mkSettings["login"], settings.mkSettings["passWd"]),
	("https://manga.madokami.com", settings.mkSettings["login"], settings.mkSettings["passWd"]),
	]

class MkFeedLoader(ScrapePlugins.RetreivalDbBase.ScraperDbBase):

	wg = webFunctions.WebGetRobust(creds=HTTPS_CREDS)
	loggerPath = "Main.Manga.Mk.Fl"
	pluginName = "Manga.Madokami Link Retreiver"
	tableKey = "mk"
	dbName = settings.DATABASE_DB_NAME

	tableName = "MangaItems"
	urlBaseManga = "https://manga.madokami.com/Manga/"
	# urlBaseManga = "http://manga.madokami.com/Manga/Admin%20Cleanup"
	urlBaseMT    = "https://manga.madokami.com/MangaTraders/"

	def checkLogin(self):
		pass

	def closeDB(self):
		self.log.info( "Closing DB...",)
		self.conn.close()
		self.log.info( "done")

	def getCharacterLut(self, soup):
		tag = soup.find("div", class_="index-container")
		if not tag or not hasattr(tag, "data-table"):
			raise ValueError("Could not find lookup table on page!")

		table = json.loads(tag["data-table"])
		lut = {}
		for x in range(len(table)):
			lut[x] = chr(table[x])
		return lut

	def parseOutLink(self, linkTag):

		# if not hasattr(linkTag, "data-enc"):
			# raise ValueError("Invalid link! Link: '%s'", linkTag)

		# data = json.loads(linkTag["data-enc"])
		# print("Link json data = ", data)

		# url  = "".join([lut[letter^0x33] for letter in data["url"]])
		url = linkTag['href']
		name = url.split("/")[-1]
		name = urllib.parse.unquote(name)

		# print("Link data = ", data)
		# print("Link url  = ", url)
		# print("Link url  = ", urllib.parse.unquote(url))
		# print("Link name = ", name)

		return url, name

	def parseRow(self, row, curUrlPath, dirName):


		if not len(row.find_all("td")) == 6:
			return None, None


		name, size, modified, tags, report, read = row.find_all("td")


		relUrl, linkName = self.parseOutLink(row.a)

		itemUrl = urllib.parse.urljoin(curUrlPath, relUrl)

		# Decompose all trailing tags (e.g. author and incomplete status info)
		# This is required to make identifying download type by trailing '/' functional
		for span in name.find_all('span'):
			span.decompose()
		if not name.get_text().strip().endswith("/"):
			item = {}

			item["date"]     = time.time()
			item["dlName"]   = linkName
			item["dlLink"]   = itemUrl
			item["baseName"] = dirName

			return None, item
		else:
			# Mask out the incoming item directories.
			if any([x in itemUrl for x in MASK_PATHS]):
				return None, None

			# Pull the name out of the URL path. I don't like doing this, but it's actually what Okawus is doing
			# to generate the pages anways, so what the hell.
			newDirName = urllib.parse.unquote(itemUrl.split("/")[-1])
			newDir = (newDirName, itemUrl)

			return newDir, None


		# else:
		# 	self.log.critical('"class" in row', "class" in row.attrs)
		# 	self.log.critical('row.attrs', row.attrs)
		# 	raise ValueError("wat?")

	def getItemsFromContainer(self, dirName, dirUrl):

		# Skip the needs sorting directory.
		if dirName == 'Needs sorting':
			return [], []
		if dirName == 'Admin Cleanup':
			return [], []
		if dirName == 'Raws':
			return [], []
		if dirName == 'Requests':
			return [], []
		if dirName == '_Autouploads':
			return [], []


		self.log.info("Original name - %s", dirName)

		bracketStripRe = re.compile(r"(\[.*?\])")
		dirName = bracketStripRe.sub(" ", dirName)
		while dirName.find("  ")+1:
			dirName = dirName.replace("  ", " ")
		dirName = dirName.strip()

		if not dirName:
			self.log.critical("Empty dirname = '%s', baseURL = '%s'", dirName, dirUrl)
			raise ValueError("No dir name for directory!")

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

			dirDat, itemDat = self.parseRow(row, dirUrl, dirName)

			if dirDat:
				dirRet.append(dirDat)

			if itemDat:
				itemRet.append(itemDat)


		return dirRet, itemRet




	def thread_go(self):

		while len(self.seriesPages) and runStatus.run:
			folderName, folderUrl = self.seriesPages.pop()


			if folderUrl in self.scanned:
				self.log.warning("Duplicate item made it into %s", folderUrl)
				continue
			try:
				newDirs, newItems = self.getItemsFromContainer(folderName, folderUrl)
			except ValueError:
				pass

			self.scanned.add(folderUrl)


			for newDir in [newD for newD in newDirs if newD not in self.scanned]:
				self.seriesPages.add(newDir)

			if newItems:
				self.processLinksIntoDB(newItems)
				for newItem in newItems:
					self.items.append(newItem)

			self.log.info("Have %s items %s total, %s pages remain to scan", len(newItems), len(self.items), len(self.seriesPages))
			if not runStatus.run:
				self.log.info("Breaking due to exit flag being set")



	def getMainItems(self):
		# for item in items:
		# 	self.log.info( item)
		#

		# Muck about in the webget internal settings
		self.wg.errorOutCount = 4
		self.wg.retryDelay    = 5

		self.log.info( "Loading Madokami Main Feed")

		self.items = []

		self.scanned = set((self.urlBaseManga, self.urlBaseMT))


		self.seriesPages, self.items = self.getItemsFromContainer("UNKNOWN", self.urlBaseManga)
		# seriesPages2, items2 = self.getItemsFromContainer("UNKNOWN", self.urlBaseMT)
		seriesPages2, items2 = [], []

		self.seriesPages = set(self.seriesPages) | set(seriesPages2)

		for page in seriesPages2:
			self.seriesPages.add(page)

		for page in items2:
			self.items.append(page)

		processes = 3

		with ThreadPoolExecutor(max_workers=processes) as executor:
			futures = [executor.submit(self.thread_go) for x in range(processes)]
			complete = [future.result() for future in futures]




	def processLinksIntoDB(self, linksDicts, isPicked=False):

		self.log.info( "Inserting...",)
		newItems = 0
		oldItems = 0
		for link in linksDicts:
			if link is None:
				print("linksDicts", linksDicts)
				print("WAT")

			rows = self.getRowsByValue(originName  = link["dlName"])    #We only look at filenames to determine uniqueness,
			if not rows:
				rows = self.getRowsByValue(sourceUrl  = link["dlLink"])    #Check against URLs as well, so we don't break the UNIQUE constraint

			if not rows:
				newItems += 1

				# Patch series name.
				seriesName = nt.getCanonicalMangaUpdatesName(link["baseName"])

				# Flags has to be an empty string, because the DB is annoying.
				# TL;DR, comparing with LIKE in a column that has NULLs in it is somewhat broken.
				self.insertIntoDb(retreivalTime = link["date"],
									sourceUrl   = link["dlLink"],
									originName  = link["dlName"],
									dlState     = 0,
									seriesName  = seriesName,
									flags       = '',
									commit      = False)  # Defer commiting changes to speed things up



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
					oldItems += 1
					# self.log.info("Existing item: %s", (link["date"], link["dlName"]))

			else:
				row = row.pop()

		self.log.info( "Done")

		if newItems:

			self.log.info( "Committing...",)
			self.conn.commit()
			self.log.info( "Committed")
		else:
			self.log.info("No new items, %s old items.", oldItems)


		return newItems


	def go(self):

		self.resetStuckItems()
		self.log.info("Getting feed items")

		feedItems = self.getMainItems()
		# self.log.info("Processing feed Items")

		# self.processLinksIntoDB(feedItems)
		self.log.info("Complete")




class Runner(ScrapePlugins.RunBase.ScraperBase):
	loggerPath = "Main.Manga.MkL.Run"

	pluginName = "MkFLoader"


	def _go(self):

		self.log.info("Checking Mk feeds for updates")
		fl = MkFeedLoader()
		fl.go()
		fl.closeDB()

if __name__ == "__main__":
	import utilities.testBase as tb

	with tb.testSetup(startObservers=False):

		run = Runner()
		run.go()

