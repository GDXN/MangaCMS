
import webFunctions
import runStatus
import re

import bs4
import urllib.parse

import time
import settings
import psycopg2
import dateutil.parser

import ScrapePlugins.MonitorDbBase
# import TextScrape.NovelMixin

def toInt(inStr):
	return int(''.join(ele for ele in inStr if ele.isdigit()))


# Maintains a local mirror of a user's watches series on mangaUpdates
# This only retreives the watched item list. ChangeMonitor.py actually fetches the metadata.
class BuWatchMonitor(ScrapePlugins.MonitorDbBase.MonitorDbBase):

	loggerPath       = "Main.Manga.Bu.Watcher"
	pluginName       = "BakaUpdates List Monitor"
	tableName        = "MangaSeries"
	nameMapTableName = "muNameList"
	changedTableName = "muItemChanged"
	itemReleases     = "muReleases"

	baseURL          = "http://www.mangaupdates.com/"
	baseListURL      = r"http://www.mangaupdates.com/mylist.html"
	baseReleasesURL  = r"https://www.mangaupdates.com/releases.html"

	dbName = settings.DATABASE_DB_NAME

	wgH = webFunctions.WebGetRobust(logPath=loggerPath+".Web")


	# -----------------------------------------------------------------------------------
	# Login Management tools
	# -----------------------------------------------------------------------------------


	def checkLogin(self):

		checkPage = self.wgH.getpage(self.baseListURL)
		if "You must be a user to access this page." in checkPage:
			self.log.info("Whoops, need to get Login cookie")
		else:
			self.log.info("Still logged in")
			return

		logondict = {"username" : settings.buSettings["login"], "password" : settings.buSettings["passWd"], "act" : "login"}
		getPage = self.wgH.getpage(r"http://www.mangaupdates.com/login.html", postData=logondict)
		if "No user found, or error. Try again." in getPage:
			self.log.error("Login failed!")
			raise ValueError("Cannot login to MangaUpdates. Is your login/password valid?")
		elif "You are currently logged in as" in getPage:
			self.log.info("Logged in successfully!")

		self.wgH.saveCookies()


	# -----------------------------------------------------------------------------------
	# Management Stuff
	# -----------------------------------------------------------------------------------


	def go(self):
		self.checkLogin()

		self.scanRecentlyUpdated()

		lists = self.getListNames()


		for listName, listURL in lists.items():
			self.updateUserListNamed(listName, listURL)

			if not runStatus.run:
				self.log.info( "Breaking due to exit flag being set")
				break


	def getListNames(self):
		self.checkLogin()

		listDict = {}
		listDict["Reading"] = r"http://www.mangaupdates.com/mylist.html"  # The reading list is not specifically named.

		pageCtnt = self.wgH.getpage(self.baseListURL)

		soup = bs4.BeautifulSoup(pageCtnt, "lxml")
		add_seriesSegment = soup.find("div", id="add_series")
		listList = add_seriesSegment.find_previous_sibling("p", class_="text")
		for item in listList("a"):
			if "mylist.html" in item["href"] and not "act=edit" in item["href"]:  # We don't want the "edit lists" list option.
				listDict[item.text] = item["href"]
		self.log.info("Retrieved %d lists", len(listDict))

		for key, value in listDict.items():
			self.log.debug("List name: %s, URL: %s", value, key)

		return listDict




	# -----------------------------------------------------------------------------------
	# Series List scraping
	# -----------------------------------------------------------------------------------

	def extractRow(self, row, listName):

		nameSegment = row.find("td", class_="lcol_nopri")
		if nameSegment:

			currentChapter = -1

			link = nameSegment.find("a")["href"]
			mangaName = nameSegment.find("a").string
			urlParsed = urllib.parse.urlparse(link)
			if nameSegment.find("span"):
				chapInfo = nameSegment.find("span").string
				currentChapter = toInt(chapInfo)

			readSegment = row.find("td", class_=re.compile("lcol4")).find("a", title="Increment Chapter")
			if readSegment:
				readChapter = toInt(readSegment.string)
			elif listName == "Complete":
				readChapter = -2
			else:
				readChapter = -1

			# Update the novel information (if it exists)
			# self.updateNovelAvailable(mangaName, currentChapter)
			# self.updateNovelRead(mangaName, readChapter)

			seriesID = toInt(urlParsed.query)
			listName = listName.replace("\u00A0"," ")

			# self.log.debug("Item info = seriesID=%s, currentChapter=%s, readChapter=%s, mangaName=%s, listName=%s", seriesID, currentChapter, readChapter, mangaName, listName)

			# Try to match new item by both ID and name.
			haveRow = self.getRowsByValue(buId=seriesID)
			haveRow2 = self.getRowsByValue(buName=mangaName)
			if not haveRow:
				haveRow = haveRow2

			if haveRow and haveRow2:
				if haveRow[0]["buId"] != haveRow2[0]["buId"]:
					print("WAT")
					print(haveRow[0]["buId"])
					print(haveRow2[0]["buId"])

			if haveRow:
				# print("HaveRow = ", haveRow)
				haveRow = haveRow.pop()

				try:
					self.updateDbEntry(haveRow["dbId"],
						commit=False,
						buName=mangaName,
						buList=listName,
						availProgress=currentChapter,
						readingProgress=readChapter,
						buId=seriesID)
				except psycopg2.IntegrityError:
					self.log.error("Failure updating item: '%s' on list '%s'", mangaName, listName)
			else:
				# ["mtList", "buList", "mtName", "mdId", "mtTags", "buName", "buId", "buTags", "readingProgress", "availProgress", "rating", "lastChanged"]

				self.insertIntoDb(commit=False,
					buName=mangaName,
					buList=listName,
					availProgress=currentChapter,
					readingProgress=readChapter,
					buId=seriesID,
					lastChanged=0,
					lastChecked=0,
					itemAdded=time.time())

			return 1


		return 0

	def updateUserListNamed(self, listName, listURL):

		pageCtnt = self.wgH.getpage(listURL)
		soup = bs4.BeautifulSoup(pageCtnt, "lxml")
		itemTable = soup.find("table", id="list_table")


		itemCount = 0
		if not itemTable:
			self.log.warn("Could not find table?")
			self.log.warn("On page '%s'", listURL)
			return
		for row in itemTable.find_all("tr"):
			itemCount += self.extractRow(row, listName)


		listTotalNo = toInt(soup.find("div", class_="low_col1").text)
		if itemCount != listTotalNo:
			self.log.error("Invalid list reported length! Items from page: %d, found items %d", listTotalNo, itemCount)
		self.conn.commit()
		self.log.info("Properly processed all items in list!")


	#

	def scanRecentlyUpdated(self):
		ONE_DAY = 60*60*24
		releases = self.wgH.getpage(self.baseReleasesURL)
		soup = bs4.BeautifulSoup(releases, "lxml")

		content = soup.find("td", {"id": "main_content"})
		titles = content.find_all("p", class_="titlesmall")
		for title in titles:
			date = title.get_text()
			date = dateutil.parser.parse(date, fuzzy=True)

			table = title.find_next_sibling("div").table
			for row in table.find_all("tr"):
				link = row.find("a", title="Series Info")

				# Need to skip rows with no links, (they're the table header)
				if link:
					mId = link["href"].split("=")[-1]


					haveRow = self.getRowByValue(buId=mId)
					if haveRow:
						checked = self.getLastCheckedFromId(mId)
						if checked + ONE_DAY < time.time():
							self.log.info("Need to check item for id '%s'", mId)
							self.updateLastCheckedFromId(mId, 0)  # Set last checked to zero, to force the next run to update the item
							# print("Checked, ", checked+ONE_DAY, "time", time.time())
							# print("row", self.getRowByValue(buId=mId))
					else:
						name = link.get_text()
						self.insertBareNameItems([(name, mId)])
						self.log.info("New series! '%s', id '%s'", name, mId)




	# -----------------------------------------------------------------------------------
	# General MangaUpdate mirroring tool (enqueues ALL the manga items!)
	# -----------------------------------------------------------------------------------

	def getSeriesFromPage(self, soup):
		itemTable = soup.find("table", class_="series_rows_table")

		rows = []
		for row in itemTable.find_all("tr"):
			if not row.find("td", class_="text"):
				continue

			tds = row.find_all("td")
			if len(tds) != 4:
				continue

			title, dummy_genre, dummy_year, dummy_rating = tds
			mId = title.a["href"].replace('https://www.mangaupdates.com/series.html?id=', '')
			# print("title", title.get_text(), mId)

			try:
				int(mId)
				rows.append((title.get_text(), mId))
			except ValueError:
				self.log.critical("Could not extract ID? TitleTD = %s", title)


		return rows

	# TODO: Schedule this occationally
	def getAllManga(self):
		urlFormat = 'https://www.mangaupdates.com/series.html?page={page}&perpage=100'
		self.log.info("MU Updater scanning MangaUpdates to get all available manga.")
		run = 456
		while run:
			url = urlFormat.format(page=run)

			run += 1

			soup = self.wgH.getSoup(url)
			series = self.getSeriesFromPage(soup)
			if series:
				self.log.info("Inserting %s items into name DB", len(series))
				self.insertBareNameItems(series)

			if len(series) == 0:
				self.log.info("No items found. At the end of the series list?")
				run = 0
			if not runStatus.run:
				self.log.info( "Breaking due to exit flag being set")
				break

		self.log.info("Completed scanning all manga items.")



if __name__ == "__main__":
	import utilities.testBase as tb

	with tb.testSetup(startObservers=False):


		mon = BuWatchMonitor()
		mon.go()
		# mon.scanRecentlyUpdated()
		# mon.getAllManga()
		mon.closeDB()

