import webFunctions

import calendar
import traceback

import json
import settings
from dateutil import parser
import urllib.parse
import time

import ScrapePlugins.LoaderBase
class DbLoader(ScrapePlugins.LoaderBase.LoaderBase):


	dbName = settings.DATABASE_DB_NAME
	loggerPath = "Main.Manga.DjM.Fl"
	pluginName = "DjMoe Link Retreiver"
	tableKey    = "djm"
	urlBase = "http://doujins.com/"

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	tableName = "HentaiItems"
	shouldCanonize = False

	def loadFeed(self, pageOverride=None):
		self.log.info("Retreiving feed content...",)
		if not pageOverride:
			pageOverride = 1
		try:
			# They're apparently sniffing cookies now. Fake out the system by loading the container page first.
			dummy_pg = self.wg.getpage("http://doujins.com/main")
			data = self.wg.getJson( urllib.parse.urljoin(self.urlBase, "/ajax/newest.php"), addlHeaders={'Referer': 'http://doujins.com/main'}, postData={'get': pageOverride} )
		except urllib.error.URLError:
			self.log.critical("Could not get feed from Doujin Moe!")
			self.log.critical(traceback.format_exc())
			return []

		try:
			self.log.info("done")
		except ValueError:
			self.log.critical("Get did not return JSON like normal!")
			self.log.critical("Returned page contents = %s", data)
			return []

		if not "success" in data or data["success"] != True:
			self.log.error("POST did not return success!")
			self.log.error("Returned JSON string = %s", data)
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
				item['retreivalTime'] = time.time()

				ret.append(item)

			except:
				self.log.info("WAT?")
				traceback.print_exc()

		return ret


if __name__ == "__main__":
	import utilities.testBase as tb

	with tb.testSetup(load=False):
		# getHistory()
		run = DjMoeDbLoader()
		# run.getFeed()
		run.go()
