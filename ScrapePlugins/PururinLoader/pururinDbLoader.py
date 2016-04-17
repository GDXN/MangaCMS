
import runStatus
runStatus.preloadDicts = False
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


	dbName = settings.DATABASE_DB_NAME
	loggerPath = "Main.Manga.Pururin.Fl"
	pluginName = "Pururin Link Retreiver"
	tableKey    = "pu"
	urlBase = "http://pururin.com/"

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	tableName = "HentaiItems"

	def loadFeed(self, pageOverride=None):
		self.log.info("Retreiving feed content...",)
		if not pageOverride:
			pageOverride = 1
		try:
			# I really don't get the logic behind Pururin's path scheme.
			if pageOverride > 1:
				urlPath = '/browse/0/1{num1}/{num2}.html'.format(num1=pageOverride-1, num2=pageOverride)
				pageUrl = urllib.parse.urljoin(self.urlBase, urlPath)
			else:
				# First page is just the bare URL. It /looks/ like they're blocking the root page by direct path.
				pageUrl = self.urlBase

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

	def getFeed(self, pageOverride=[None]):
		# for item in items:
		# 	self.log.info(item)
		#

		self.wg.stepThroughCloudFlare("http://pururin.com/", titleContains="Pururin")

		ret = []

		for x in pageOverride:
			page = self.loadFeed(x)

			soup = bs4.BeautifulSoup(page, "lxml")

			mainSection = soup.find("ul", class_="gallery-list")

			doujinLink = mainSection.find_all("li", class_="gallery-block")

			for linkLi in doujinLink:
				tmp = self.parseLinkLi(linkLi)
				ret.append(tmp)

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
		dat = self.getFeed(list(range(50)))
		# dat = self.getFeed()
		self.processLinksIntoDB(dat)

		# for x in range(10):
		# 	dat = self.getFeed(pageOverride=x)
		# 	self.processLinksIntoDB(dat)



if __name__ == "__main__":
	import utilities.testBase as tb

	with tb.testSetup(startObservers=False):

		run = PururinDbLoader()
		run.go()

