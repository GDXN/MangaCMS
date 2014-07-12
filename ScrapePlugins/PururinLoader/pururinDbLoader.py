import webFunctions

import calendar
import traceback

import bs4
import settings
from dateutil import parser
import urllib.parse
import time

import ScrapePlugins.RetreivalDbBase
class PururinDbLoader(ScrapePlugins.RetreivalDbBase.ScraperDbBase):

	wg = webFunctions.WebGetRobust()

	dbName = settings.dbName
	loggerPath = "Main.Pururin.Fl"
	pluginName = "Pururin Link Retreiver"
	tableKey    = "pu"
	urlBase = "http://pururin.com/"



	def loadFeed(self, pageOverride=None):
		self.log.info("Retreiving feed content...",)
		if not pageOverride:
			pageOverride = 1
		try:
			# I really don't get the logic behind Pururin's path scheme.
			urlPath = '/browse/0/1{num1}/{num2}.html'.format(num1=pageOverride-1, num2=pageOverride)
			pageUrl = urllib.parse.urljoin(self.urlBase, urlPath)
			print("Fetching page at", pageUrl)
			page = self.wg.getpage(pageUrl)
		except urllib.error.URLError:
			self.log.critical("Could not get page from Pururin!")
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

		mainSection = soup.find("ul", class_="gallery-list")
		doujinLink = mainSection.find_all("li", class_="gallery-block")

		ret = []
		for linkLi in doujinLink:
			ret.append(self.parseLinkLi(linkLi))

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
