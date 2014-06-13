
import webFunctions
import runStatus
import sys

import bs4
import urllib.parse

import time
import settings


import ScrapePlugins.MonitorDbBase

CHECK_INTERVAL = 60 * 60 * 24 *3  # Every 3 days

def toInt(inStr):
	return int(''.join(ele for ele in inStr if ele.isdigit()))

class BuDateUpdater(ScrapePlugins.MonitorDbBase.MonitorDbBase):

	loggerPath = "Main.Bu.DateUpdater"
	pluginName = "BakaUpdates Update Date Monitor"
	tableName = "MangaSeries"

	baseURL = "http://www.mangaupdates.com/"
	itemURL = 'http://www.mangaupdates.com/series.html?id={buId}'


	dbName = settings.dbName

	wgH = webFunctions.WebGetRobust()



	def go(self):
		items = self.getItemsToCheck()

		# lists = {"Win": r"http://www.mangaupdates.com/mylist.html?list=user11"}
		# lists = {"Unfinished": r"http://www.mangaupdates.com/mylist.html?list=unfinished"}
		# lists = {"Complete": r"http://www.mangaupdates.com/mylist.html?list=complete"}

		for dbId, mId in items:
			self.updateItem(dbId, mId)

		# dbId, mId = items.pop()
		# self.updateItem(dbId, mId)
		# print("Item ID = ", dbId, mId)

		# dbId, mId = items.pop()
		# print("Item ID = ", dbId, mId)
		# self.updateItem(dbId, mId)

		# self.downloadNewFiles(idOverride=idOverride, limit=limit)


	def getItemsToCheck(self):

		cur = self.conn.cursor()
		ret = cur.execute('''SELECT dbId,buId FROM {tableName} WHERE (lastChecked < ? or lastChecked IS NULL) and buId IS NOT NULL LIMIT 50;'''.format(tableName=self.tableName), (time.time()-CHECK_INTERVAL,))
		rets = ret.fetchall()

		return rets

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



	def updateItem(self, dbId, mId):

		pageCtnt = self.wgH.getpage(self.itemURL.format(buId=mId))
		soup = bs4.BeautifulSoup(pageCtnt)

		release = self.getLatestRelease(soup)
		tags = self.extractTags(soup)
		genres =  self.extractGenres(soup)

		kwds = {
			"lastChecked" : time.time()
		}
		if release:
			kwds["lastChanged"] = release

		if tags:
			kwds["buTags"] = " ".join(tags)
		if genres:
			kwds["buGenre"] = " ".join(genres)


		self.updateDbEntry(dbId, **kwds)



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
			with open("pageTemp.html", "wb") as fp:
				fp.write(getPage)
		elif "You are currently logged in as" in getPage:
			self.log.info("Logged in successfully!")

		self.wgH.saveCookies()


		# checkPage = self.wgH.getpage(self.baseListURL)
		# if "You must be a user to access this page." in checkPage:
		# 	self.log.info("Still not logged in?")
