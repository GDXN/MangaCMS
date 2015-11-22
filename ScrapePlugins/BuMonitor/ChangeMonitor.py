
import webFunctions
import runStatus
import urllib.parse
import re
import bs4
import traceback
import random
from concurrent.futures import ThreadPoolExecutor
import time
import settings

import os.path
import ScrapePlugins.MonitorDbBase

# Check items on user's watched list for changes every day
CHECK_INTERVAL       = 60 * 60 * 24 *  3  # Every 3 days

# check all MT items for changes once per month
CHECK_INTERVAL_OTHER = 60 * 60 * 24 * 30  # Every month

def toInt(inStr):
	return int(''.join(ele for ele in inStr if ele.isdigit()))

class BuDateUpdater(ScrapePlugins.MonitorDbBase.MonitorDbBase):

	loggerPath       = "Main.Manga.Bu.DateUpdater"
	pluginName       = "BakaUpdates Update Date Monitor"
	tableName        = "MangaSeries"
	nameMapTableName = "muNameList"
	changedTableName = "muItemChanged"
	itemReleases     = "muReleases"

	baseURL          = "http://www.mangaupdates.com/"
	itemURL          = 'http://www.mangaupdates.com/series.html?id={buId}'



	dbName = settings.DATABASE_DB_NAME

	wgH = webFunctions.WebGetRobust(logPath=loggerPath+".Web")



	# https://www.mangaupdates.com/series.html?page=2&letter=A&perpage=100


	goBigThreads = 16
	# goBigThreads = 1


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
		self.checkItems(items)

	def gobig(self):
		self.log.info("Going big! Running ALL THE THREADS!")
		self.checkLogin()
		items = self.getItemsToCheck(noLimit=True, allTheItems=True)

		self.log.info("Number of items to check: '%s'", len(items))

		if items:
			def iter_baskets_from(items, maxbaskets=3):
				'''generates evenly balanced baskets from indexable iterable'''
				item_count = len(items)
				baskets = min(item_count, maxbaskets)
				for x_i in range(baskets):
					yield [items[y_i] for y_i in range(x_i, item_count, baskets)]

			linkLists = iter_baskets_from(items, maxbaskets=self.goBigThreads)

			with ThreadPoolExecutor(max_workers=self.goBigThreads) as executor:

				for linkList in linkLists:
					executor.submit(self.checkItems, linkList)

				executor.shutdown(wait=True)




	def checkItems(self, items):

		totItems = len(items)
		scanned = 0
		while items:
			dbId, mId = items.pop(0)
			try:
				self.updateItem(dbId, mId)
			except KeyboardInterrupt:
				raise
			except:
				self.log.critical("ERROR?")
				self.log.critical(traceback.format_exc())

			scanned += 1
			self.log.info("Scanned %s of %s manga pages. %s%% done.", scanned, totItems, (1.0*scanned)/totItems*100)
			if not runStatus.run:
				self.log.info( "Breaking due to exit flag being set")
				break


	def getItemsToCheck(self, noLimit=False, allTheItems=False):

		if noLimit:
			limitStr = ""
		else:
			limitStr = "LIMIT 500"


		with self.conn.cursor() as cur:
			with self.transaction() as cur:
				if not allTheItems:
					ret = cur.execute('''SELECT dbId,buId
											FROM {tableName}
											WHERE
												(lastChecked < %s or lastChecked IS NULL)
												AND buId IS NOT NULL
												AND buList IS NOT NULL
											{limitStr} ;'''.format(tableName=self.tableName, limitStr=limitStr), (time.time()-CHECK_INTERVAL,))
					rets = cur.fetchall()

					# Only process non-list items if there are no list-items to process.
					if len(rets) < 50:

						ret = cur.execute('''SELECT dbId,buId
												FROM {tableName}
												WHERE
													(lastChecked < %s or lastChecked IS NULL)
													AND buId IS NOT NULL
													AND buList IS NULL
												{limitStr} ;'''.format(tableName=self.tableName, limitStr=limitStr), (time.time()-CHECK_INTERVAL_OTHER,))
						rets2 = cur.fetchall()
						for row in rets2:
							rets.append(row)
				else:  # AllTheItems:
					ret = cur.execute('''SELECT dbId,buId FROM {tableName} WHERE buId IS NOT NULL;'''.format(tableName=self.tableName))
					rets = cur.fetchall()

			cur.execute("COMMIT;")
		self.log.info("Items to check = %s", len(rets))
		return rets


	def getItemInfo(self, dbId, mId):

		pageCtnt  = self.wgH.getpage(self.itemURL.format(buId=mId))

		if "You specified an invalid series id." in pageCtnt:
			self.log.warning("Invalid MU ID! ID: %s", mId)
			self.deleteRowByBuId(mId)
			return False, False

		soup      = bs4.BeautifulSoup(pageCtnt)

		release   = self.getLatestRelease(soup)
		availProg = self.getAvailProgress(soup)
		tags      = self.fetchTags(mId, soup)
		genres    = self.extractGenres(soup)
		mngType   = self.getType(soup)

		author    = self.getAuthor(soup)
		artist    = self.getArtist(soup)
		desc      = self.getDescription(soup)
		relState  = self.getReleaseState(soup)


		baseName, altNames = self.getNames(soup)
		# print("Basename = ", baseName)
		self.log.info("Basename = %s, AltNames = %s", baseName, altNames)
		self.log.info("Author = %s, Artist = %s", author, artist)
		self.log.info("ReleaseState %s, desc len = %s, type = %s", relState, len(desc), mngType)
		kwds = {
			"lastChecked"   : time.time(),
			"buName"        : baseName,
			"buArtist"      : artist,
			"buAuthor"      : author,
			"buDescription" : desc,
			"buRelState"    : relState,
			"buType"        : mngType
		}
		if release:
			kwds["lastChanged"] = release

		if availProg:
			kwds["availProgress"] = availProg

		if tags:
			kwds["buTags"] = " ".join(tags)
		if genres:
			kwds["buGenre"] = " ".join(genres)


		return kwds, altNames

		# Retreive page for mId, extract relevant information, and update the DB with the scraped info
	def updateItem(self, dbId, mId):

		kwds, altNames = self.getItemInfo(dbId, mId)
		if not kwds:
			return

		# if kwds['buType'] == 'Novel':
		# 	self.upsertNovelName(kwds['buName'])
		# 	if 'availProgress' in kwds:
		# 		self.updateNovelAvailable(kwds['buName'], kwds['availProgress'])
		# 	if 'buTags' in kwds:
		# 		self.updateNovelTags(kwds['buName'], kwds['buTags'])
		# 	if 'buGenre' in kwds:
		# 		self.updateNovelTags(kwds['buName'], kwds['buGenre'])


		haveRows = self.getRowByValue(buName=kwds['buName'])

		if haveRows and haveRows["dbId"] != dbId:

			self.log.error("Multiple items for the same row?")
			self.log.error("Insert will collide!")
			self.deleteRowByBuId(haveRows["dbId"])
			self.insertBareNameItems([("UNKNOWN - {buId}".format(buId=haveRows["buId"]), haveRows["buId"])])

		self.insertNames(mId, altNames)

		self.updateDbEntry(dbId, **kwds)

	# -----------------------------------------------------------------------------------
	# Series Page Scraping
	# -----------------------------------------------------------------------------------

	def getAvailProgress(self, soup):
		item = soup.find("a", text=re.compile("Search for all releases of this series", re.IGNORECASE))
		if not item:
			return None
		searchPage = item['href']

		relPage = self.wgH.getSoup(searchPage)

		mainTd = relPage.find('td', id='main_content')

		# This is HORRIBLE, but MangaUpdates uses NO decent anchor information.
		mainTd = mainTd.find('table', border="0", cellpadding="0", cellspacing="0", width="100%")
		mainTd = mainTd.table.table

		# Top two rows are the header, and a spacer. Dump them.
		mainTd.tr.decompose()
		mainTd.tr.decompose()

		avail = 0
		maxAvail = 2**30
		chap  = 0
		for row in mainTd.find_all("tr"):
			ctnt = row.find_all("td")

			if len(ctnt) != 5:
				print("Skipping row?")
				continue
			ulDate, sLink, vol, chap, group = ctnt
			chap = chap.get_text()

			chap = ''.join([c if c in '1234567890' else ' ' for c in chap])
			chap = chap.strip()
			# Handle things like 'extra' for the volume, etc...
			if chap:
				chap = chap.split()[0]
			else:
				chap = 0
			chap = int(chap)
			if chap > avail:
				avail = chap
			if chap and chap < maxAvail:
				maxAvail = chap

		if maxAvail > 2**24:
			maxAvail = "NaN"
		self.log.info("Available progress: %s chapters (min %s)", avail, maxAvail)

		if avail == 0:
			return None
		return avail


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


	def fetchTags(self, mId, soup):

		# https://www.mangaupdates.com/ajax/show_categories.php?s=81129&type=1&cache_j=33680585,60978550,84319640

		# url += "&cache_j=" + Math.floor(Math.random()*100000000) + "," + Math.floor(Math.random()*100000000) + "," + Math.floor(Math.random()*100000000)

		tagAjaxUrl = 'https://www.mangaupdates.com/ajax/show_categories.php?s={mId}&type={type}&cache_j={num1},{num2},{num3}'.format(mId=mId,
																																	type=1,
																																	num1=int(random.random()*100000000),
																																	num2=int(random.random()*100000000),
																																	num3=int(random.random()*100000000))

		soup = self.wgH.getSoup(tagAjaxUrl, addlHeaders={'Referer': self.itemURL.format(buId=mId)})

		tagsHeaderB = soup.find("div", id="cat_opts")

		if not tagsHeaderB:
			return []

		if (not "Vote these categories" in soup.get_text()) and (not "Log in to vote!" in soup.get_text()):
			return []

		container = soup.find("ul")


		tags = container.find_all("li")

		if not tags:
			return []

		tags = [tag.get_text() for tag in tags]

		outList = []
		for tag in tags:
			outList.append(tag.replace(" ", "-"))

		self.log.info("Item has %s tags.", len(tags))
		return outList




	def getNames(self, soup):
		namePostfixes = ['(Russian)', '(Arabic)', '(Thai)', '(Chinese)', '(Japanese)', '(Korean)', '(Polish)', '(Spanish)', '(Portugese)', '(English)', '(Italian)', '(French)']
		baseNameContainer = soup.find("span", class_="releasestitle tabletitle")
		baseName = baseNameContainer.get_text()

		namesHeaderB = soup.find("b", text="Associated Names")
		container = namesHeaderB.parent.find_next_sibling("div", class_="sContent")

		altNames = [baseName]

		for name in container.find_all(text=True):
			name = name.rstrip().lstrip()
			if name:
				altNames.append(name)

			# Some of the names are cluttered up by their language of origin. Strip that cruft out,
			# and add the cleaned name if it's different.
			# I'm making a big assumption here that there are no cases where
			# the langauge is actually part of the title, but I think that's probably fairly safe?
			for postfix in namePostfixes:
				if name.endswith(postfix):
					name = name[:-1*len(postfix)]
					if name and not name in altNames:
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

	def getType(self, soup):

		header = soup.find("b", text="Type")
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

		return "%s" % container.prettify()


	def getReleaseState(self, soup):
		header = soup.find("b", text="Status in Country of Origin")
		if not header:
			return ""

		container = header.parent.find_next_sibling("div", class_="sContent")
		if not container:
			return ""

		return " ".join(container.strings).strip().strip(" ,")



if __name__ == "__main__":
	import utilities.testBase as tb

	with tb.testSetup(startObservers=False):

		run = BuDateUpdater()
		run.checkLogin()
		# ret1, ret2 = run.getItemInfo("81129")
		# ret1, ret2 = run.getItemInfo("120125")
		# print(ret1)
		# print(ret2)
		# run.updateItem(101, "45918")
		# run.go()
		run.gobig()

