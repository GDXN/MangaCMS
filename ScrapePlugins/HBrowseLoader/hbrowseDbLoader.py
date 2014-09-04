import webFunctions

import calendar
import traceback

import bs4
import settings
from dateutil import parser
import urllib.parse
import time

import ScrapePlugins.RetreivalDbBase
class HBrowseDbLoader(ScrapePlugins.RetreivalDbBase.ScraperDbBase):


	dbName = settings.dbName
	loggerPath = "Main.HBrowse.Fl"
	pluginName = "H-Browse Link Retreiver"
	tableKey    = "hb"
	urlBase = "http://www.hbrowse.com/"
	urlFeed = "http://www.hbrowse.com/list"

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	tableName = "HentaiItems"

	def loadFeed(self, pageOverride=None):
		self.log.info("Retreiving feed content...",)
		if not pageOverride:
			pageOverride = 1
		try:
			# I really don't get the logic behind HBrowse's path scheme.
			urlPath = '/list/{num}'.format(num=pageOverride)
			pageUrl = urllib.parse.urljoin(self.urlBase, urlPath)
			print("Fetching page at", pageUrl)
			page = self.wg.getpage(pageUrl)
		except urllib.error.URLError:
			self.log.critical("Could not get page from HBrowse!")
			self.log.critical(traceback.format_exc())
			return ""

		return page



	def parseLinkLi(self, linkLi):
		ret = {}
		ret["dlName"] = " / ".join(linkLi.h2.strings) # Messy hack to replace <br> tags with a ' / "', rather then just removing them.
		ret["pageUrl"] = urllib.parse.urljoin(self.urlBase, linkLi.a["href"])
		return ret

	def getFeed(self, pageOverride=None):
		# for item in items:
		# 	self.log.info(item)
		#

		page = self.loadFeed(pageOverride)

		soup = bs4.BeautifulSoup(page)

		itemTable = soup.find("table", id="recentTable")

		rows = itemTable.find_all("tr")

		ret = []
		for row in rows:

			if not "onmouseover" in row.attrs:
				print("Row", row)
			# ret.append(self.parseLinkLi(linkLi))

		return ret



	def processLinksIntoDB(self, linksDict):
		self.log.info("Inserting...")

		newItemCount = 0

		for link in linksDict:

			row = self.getRowsByValue(sourceUrl=link["pageUrl"])
			if not row:
				curTime = time.time()
				self.insertIntoDb(retreivalTime=curTime, sourceUrl=link["pageUrl"], originName=link["dlName"], dlState=0)
				# cur.execute('INSERT INTO fufufuu VALUES(?, ?, ?, "", ?, ?, "", ?);',(link["date"], 0, 0, link["dlLink"], link["itemTags"], link["dlName"]))
				self.log.info("New item: %s", (curTime, link["pageUrl"], link["dlName"]))



		self.log.info("Done")
		self.log.info("Committing...",)
		self.conn.commit()
		self.log.info("Committed")

		return newItemCount


	def go(self):
		self.resetStuckItems()
		dat = self.getFeed()
		self.processLinksIntoDB(dat)

		# for x in range(10):
		# 	dat = self.getFeed(pageOverride=x)
		# 	self.processLinksIntoDB(dat)
