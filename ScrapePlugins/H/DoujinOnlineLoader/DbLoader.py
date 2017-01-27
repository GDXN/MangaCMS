
import runStatus
runStatus.preloadDicts = False
import webFunctions

import calendar
import traceback

import re
import settings
from dateutil import parser
import urllib.parse
import time

import ScrapePlugins.RetreivalDbBase
class DbLoader(ScrapePlugins.RetreivalDbBase.ScraperDbBase):


	dbName = settings.DATABASE_DB_NAME
	loggerPath = "Main.Manga.DoujinOnline.Fl"
	pluginName = "DoujinOnline Link Retreiver"
	tableKey    = "dol"
	urlBase = "https://doujinshi.online/"

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	tableName = "HentaiItems"

	def loadFeed(self, pageOverride=None):
		self.log.info("Retreiving feed content...",)
		if not pageOverride:
			pageOverride = 1

		urlPath = '/page/{num}/'.format(num=pageOverride)
		sourceUrl = urllib.parse.urljoin(self.urlBase, urlPath)

		page = self.wg.getSoup(sourceUrl)

		return page



	def parseLinkDiv(self, linkdiv):


		dated = linkdiv.find("div", class_="dou-date")
		titled = linkdiv.find("div", class_="dou-title")
		langd = linkdiv.find("div", class_="lang-icon")


		if not all([langd, titled, dated]):
			return

		if not langd.img:
			return
		if not langd.img['src'].endswith("en.png"):
			return


		ret = {}


		ret["originName"] = titled.get_text().strip()
		ret["sourceUrl"] = urllib.parse.urljoin(self.urlBase, titled.a["href"])


		pdate = parser.parse(dated.get_text())
		ret["retreivalTime"] = calendar.timegm(pdate.utctimetuple())

		# print("ret = ", ret)
		# print(pdate, dated.get_text())
		# return

		return ret

	def getFeed(self, pageOverride=[None]):
		# for item in items:
		# 	self.log.info(item)
		#

		# self.wg.stepThroughCloudFlare("https://DoujinOnline.la/", titleContains="DoujinOnline.la")

		ret = []

		for x in pageOverride:
			soup = self.loadFeed(x)

			doujinLink = soup.find_all("div", class_="dou-list")

			for linkLi in doujinLink:
				tmp = self.parseLinkDiv(linkLi)
				if tmp:
					ret.append(tmp)

		return ret




	def go(self):
		self.resetStuckItems()
		# dat = self.getFeed(list(range(50)))
		dat = self.getFeed()
		self.processLinksIntoDB(dat)

		# for x in range(10):
		# 	dat = self.getFeed(pageOverride=x)
		# 	self.processLinksIntoDB(dat)




if __name__ == "__main__":
	import utilities.testBase as tb

	with tb.testSetup(startObservers=False, load=False):

		run = DbLoader()
		# dat = run.getFeed(pageOverride=[1])
		# print(dat)
		# run.go()

		from concurrent.futures import ThreadPoolExecutor


		def callable_f(baseclass, page):

			dat = baseclass.getFeed(pageOverride=[page])
			baseclass.processLinksIntoDB(dat)
		with ThreadPoolExecutor(max_workers=5) as ex:
			for x in range(1160):
				ex.submit(callable_f, run, x)

