import webFunctions

import calendar
import traceback

import json
import settings
from dateutil import parser
import urllib.parse
import time

import ScrapePlugins.RetreivalDbBase
class DjMoeDbLoader(ScrapePlugins.RetreivalDbBase.ScraperDbBase):


	dbName = settings.DATABASE_DB_NAME
	loggerPath = "Main.Manga.DjM.Fl"
	pluginName = "DjMoe Link Retreiver"
	tableKey    = "djm"
	urlBase = "http://www.doujin-moe.us/"

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	tableName = "HentaiItems"
	shouldCanonize = False

	def loadFeed(self, pageOverride=None):
		self.log.info("Retreiving feed content...",)
		if not pageOverride:
			pageOverride = 1
		try:
			# They're apparently sniffing cookies now. Fake out the system by loading the container page first.
			dummy_pg = self.wg.getpage("http://www.doujin-moe.us/main")
			data = self.wg.getJson( urllib.parse.urljoin(self.urlBase, "/ajax/newest.php"), addlHeaders={'Referer': 'http://www.doujin-moe.us/main'}, postData={'get': pageOverride} )
		except urllib.error.URLError:
			self.log.critical("Could not get feed from Doujin Moe!")
			self.log.critical(traceback.format_exc())
			return []

		try:
			self.log.info("done")
		except ValueError:
			self.log.critical("Get did not return JSON like normal!")
			self.log.critical("Returned page contents = %s", feed)
			return []

		if not "success" in data or data["success"] != True:
			self.log.error("POST did not return success!")
			self.log.error("Returned JSON string = %s", feed)
			return []

		items = data["newest"]
		return items


	def getFeed(self, pageOverride=None):
		# for item in items:
		# 	self.log.info(item)
		#

		items = self.loadFeed(pageOverride)
		ret = []
		for feedEntry in items:
			item = {}

			try:
				item["dlName"] = feedEntry["name"]
				item["contentID"] = feedEntry["token"]
				item["date"] = calendar.timegm(parser.parse( feedEntry["date"]).utctimetuple())
				#self.log.info("date = ", feedEntry['published_parsed'])

				ret.append(item)

			except:
				self.log.info("WAT?")
				traceback.print_exc()

		return ret



	def processLinksIntoDB(self, linksDict):
		self.log.info("Inserting...")

		newItemCount = 0

		for link in linksDict:

			row = self.getRowsByValue(sourceUrl=link["contentID"])
			if not row:
				curTime = time.time()
				self.insertIntoDb(retreivalTime=curTime, sourceUrl=link["contentID"], originName=link["dlName"], dlState=0)
				# cur.execute('INSERT INTO fufufuu VALUES(?, ?, ?, "", ?, ?, "", ?);',(link["date"], 0, 0, link["dlLink"], link["itemTags"], link["dlName"]))
				self.log.info("New item: %s", (curTime, link["contentID"], link["dlName"]))



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


if __name__ == "__main__":
	import utilities.testBase as tb

	with tb.testSetup(startObservers=False):
		# getHistory()
		run = DjMoeDbLoader()
		# run.getFeed()
		run.go()
