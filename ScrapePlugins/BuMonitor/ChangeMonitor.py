
import webFunctions
import runStatus
import sys

import bs4
import urllib.parse

import time
import settings

# TODO: Drive change monitoring by watching
# https://www.mangaupdates.com/releases.html



import ScrapePlugins.MonitorDbBase

# Check items on user's watched list for changes every day
CHECK_INTERVAL       = 60 * 60 * 24 *  3  # Every 3 days

# check all MT items for changes once per month
CHECK_INTERVAL_OTHER = 60 * 60 * 24 * 30  # Every month

def toInt(inStr):
	return int(''.join(ele for ele in inStr if ele.isdigit()))

class BuDateUpdater(ScrapePlugins.MonitorDbBase.MonitorDbBase):

	loggerPath       = "Main.Bu.DateUpdater"
	pluginName       = "BakaUpdates Update Date Monitor"
	tableName        = "MangaSeries"
	nameMapTableName = "muNameList"
	changedTableName = "muItemChanged"

	baseURL          = "http://www.mangaupdates.com/"
	itemURL          = 'http://www.mangaupdates.com/series.html?id={buId}'



	dbName = settings.dbName

	wgH = webFunctions.WebGetRobust()



	# https://www.mangaupdates.com/series.html?page=2&letter=A&perpage=100




	# -----------------------------------------------------------------------------------
	# Login Management tools
	# -----------------------------------------------------------------------------------

	def checkLogin(self):

		checkPage = self.wgH.getpage(r"http://www.mangaupdates.com/mylist.html")
		if "You must be a user to access this page." in checkPage:
			self.log.info("Whoops, need to get Login cookie")
		else:
			self.log.info("Still logged in")
			return

		logondict = {"username" : settings.buSettings["login"], "password" : settings.buSettings["passWd"], "act" : "login"}
		getPage = self.wgH.getpage(r"http://www.mangaupdates.com/login.html", postData=logondict)
		if "No user found, or error. Try again." in getPage:
			self.log.error("Login failed!")
			with open("pageTemp.html", "wb") as fp:
				fp.write(getPage)
		elif "You are currently logged in as" in getPage:
			self.log.info("Logged in successfully!")

		self.wgH.saveCookies()


	# -----------------------------------------------------------------------------------
	# Management Stuff
	# -----------------------------------------------------------------------------------

	def go(self):
		self.checkLogin()
		items = self.getItemsToCheck()
		totItems = len(items)
		scanned = 0
		for dbId, mId in items:
			self.updateItem(dbId, mId)
			scanned += 1
			self.log.info("Scanned %s of %s manga pages. %s%% done.", scanned, totItems, (1.0*scanned)/totItems*100)
			if not runStatus.run:
				self.log.info( "Breaking due to exit flag being set")
				break

	def getItemsToCheck(self):

		cur = self.conn.cursor()
		ret = cur.execute('''SELECT dbId,buId
								FROM {tableName}
								WHERE
									(lastChecked < %s or lastChecked IS NULL)
									AND buId IS NOT NULL
									AND buList IS NOT NULL
								LIMIT 100 ;'''.format(tableName=self.tableName), (time.time()-CHECK_INTERVAL,))
		rets = cur.fetchall()

		# Only process non-list items if there are no list-items to process.
		if len(rets) < 50:

			ret = cur.execute('''SELECT dbId,buId
									FROM {tableName}
									WHERE
										(lastChecked < %s or lastChecked IS NULL)
										AND buId IS NOT NULL
										AND buList IS NULL
									LIMIT 500;'''.format(tableName=self.tableName), (time.time()-CHECK_INTERVAL_OTHER,))
			rets2 = cur.fetchall()
			for row in rets2:
				rets.append(row)

		self.log.info("Items to check = %s", len(rets))
		return rets

		# Retreive page for mId, extract relevant information, and update the DB with the scraped info
	def updateItem(self, dbId, mId):

		pageCtnt  = self.wgH.getpage(self.itemURL.format(buId=mId))

		if "You specified an invalid series id." in pageCtnt:
			self.deleteRowById(dbId)
			self.log.warning("Invalid MU ID! ID: %s", mId)
			return

		soup      = bs4.BeautifulSoup(pageCtnt)

		release   = self.getLatestRelease(soup)
		tags      = self.extractTags(soup)
		genres    = self.extractGenres(soup)

		author    = self.getAuthor(soup)
		artist    = self.getArtist(soup)
		desc      = self.getDescription(soup)
		relState  = self.getReleaseState(soup)


		baseName, altNames = self.getNames(soup)
		# print("Basename = ", baseName)
		self.log.info("Basename = %s, AltNames = %s", baseName, altNames)
		self.log.info("Author = %s, Artist = %s", author, artist)
		self.log.info("ReleaseState %s, desc len = %s", relState, len(desc))
		kwds = {
			"lastChecked"   : time.time(),
			"buName"        : baseName,
			"buArtist"      : artist,
			"buAuthor"      : author,
			"buDescription" : desc,
			"buRelState"    : relState
		}
		if release:
			kwds["lastChanged"] = release

		if tags:
			kwds["buTags"] = " ".join(tags)
		if genres:
			kwds["buGenre"] = " ".join(genres)



		self.insertNames(mId, altNames)

		self.updateDbEntry(dbId, **kwds)

	# -----------------------------------------------------------------------------------
	# Series Page Scraping
	# -----------------------------------------------------------------------------------


	def getLatestRelease(self, soup):

		releaseHeaderB = soup.find("b", text="Latest Release(s)")

		if not releaseHeaderB:
			return None

		container = releaseHeaderB.parent.find_next_sibling("div", class_="sContent")

		if not container or not "Search for all releases of this series" in container.get_text():
			return None

		releases = container.find_all("span")

		if not releases:
			return None


		timeStamp = [str(release.get_text()) for release in releases]

		latestRelease = 0

		for release in timeStamp:
			uploadTime = ''.join([c for c in release if c in '1234567890'])
			if not uploadTime:
				continue
			uploadTime = int(uploadTime)
			uploadTime = uploadTime * 60 * 60 * 24  # Convert to seconds
			uploadTs = time.time() - uploadTime
			if uploadTs > latestRelease:
				latestRelease = uploadTs

		if latestRelease == 0:
			return None

		return latestRelease

	def extractGenres(self, soup):

		releaseHeaderB = soup.find("b", text="Genre")
		if not releaseHeaderB:
			return []

		container = releaseHeaderB.parent.find_next_sibling("div", class_="sContent")

		if not container or not "Search for series of same genre(s)" in container.get_text():
			return []

		genres = container.find_all("u")

		if not genres:
			return []

		genres = [str(genre.get_text()) for genre in genres]

		outList = []
		for genre in genres:
			if genre == "Search for series of same genre(s)":
				continue
			outList.append(genre.replace(" ", "-"))
		return outList


	def extractTags(self, soup):

		tagsHeaderB = soup.find("b", text="Categories")

		if not tagsHeaderB:
			return []

		container = tagsHeaderB.parent.find_next_sibling("div", class_="sContent")

		if not container and not "Vote these categories" in container.get_text():
			return []

		tags = container.find_all("li")

		if not tags:
			return []

		tags = [tag.get_text() for tag in tags]

		outList = []
		for tag in tags:
			outList.append(tag.replace(" ", "-"))
		return outList

	def getNames(self, soup):
		baseNameContainer = soup.find("span", class_="releasestitle tabletitle")
		baseName = baseNameContainer.get_text()

		namesHeaderB = soup.find("b", text="Associated Names")
		container = namesHeaderB.parent.find_next_sibling("div", class_="sContent")

		altNames = [baseName]

		for name in container.find_all(text=True):
			name = name.rstrip().lstrip()
			if name:
				altNames.append(name)


		return baseName, altNames

	def getAuthor(self, soup):

		header = soup.find("b", text="Author(s)")
		if not header:
			return ""

		container = header.parent.find_next_sibling("div", class_="sContent")
		if not container:
			return ""


		return ", ".join(container.strings).strip().strip(" ,")

	def getArtist(self, soup):
		header = soup.find("b", text="Artist(s)")
		if not header:
			return ""

		container = header.parent.find_next_sibling("div", class_="sContent")
		if not container:
			return ""

		return ", ".join(container.strings).strip().strip(" ,")

	def getDescription(self, soup):
		header = soup.find("b", text="Description")
		if not header:
			return ""

		container = header.parent.find_next_sibling("div", class_="sContent")
		if not container:
			return ""

		return " ".join(container.strings).strip().strip(" ,")


	def getReleaseState(self, soup):
		header = soup.find("b", text="Status in Country of Origin")
		if not header:
			return ""

		container = header.parent.find_next_sibling("div", class_="sContent")
		if not container:
			return ""

		return " ".join(container.strings).strip().strip(" ,")


