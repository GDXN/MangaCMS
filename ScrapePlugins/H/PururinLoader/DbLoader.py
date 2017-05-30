
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

import ScrapePlugins.LoaderBase
class DbLoader(ScrapePlugins.LoaderBase.LoaderBase):


	dbName = settings.DATABASE_DB_NAME
	loggerPath = "Main.Manga.Pururin.Fl"
	pluginName = "Pururin Link Retreiver"
	tableKey    = "pu"
	urlBase = "http://pururin.us/"

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	tableName = "HentaiItems"

	def loadFeed(self, pageOverride=None):
		self.log.info("Retreiving feed content...",)
		if not pageOverride:
			pageOverride = 1
		try:
			# I really don't get the logic behind Pururin's path scheme.
			if pageOverride > 1:

				urlPath = '/browse/newest?page={num}'.format(num=pageOverride)
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



	def parseLinkLi(self, linkdiv):
		ret = {}
		ret["originName"] = " / ".join(linkdiv.find("div", class_='title').strings) # Messy hack to replace <br> tags with a ' / "', rather then just removing them.
		ret["sourceUrl"] = urllib.parse.urljoin(self.urlBase, linkdiv["href"])
		ret["retreivaltime"] = time.time()

		return ret

	def getFeed(self, pageOverride=[None]):
		# for item in items:
		# 	self.log.info(item)
		#


		ret = []

		for x in pageOverride:
			page = self.loadFeed(x)

			soup = bs4.BeautifulSoup(page, "lxml")

			mainSection = soup.find("div", class_="gallery-listing")

			doujinLink = mainSection.find_all("a", class_="thumb-pururin")

			for linkLi in doujinLink:
				tmp = self.parseLinkLi(linkLi)
				ret.append(tmp)

		return ret



	def setup(self):
		self.wg.stepThroughCloudFlare("http://pururin.us/", titleContains="Pururin")





if __name__ == "__main__":
	import utilities.testBase as tb

	with tb.testSetup(load=False):

		run = DbLoader()
		# run.go()
		for x in range(1000):
			dat = run.getFeed(pageOverride=[x])
			print("Found %s items" % len(dat))
			run._processLinksIntoDB(dat)

