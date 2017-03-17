
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

import ScrapePlugins.LoaderBase
class DbLoader(ScrapePlugins.LoaderBase.LoaderBase):


	dbName = settings.DATABASE_DB_NAME
	loggerPath = "Main.Manga.Hitomi.Fl"
	pluginName = "Hitomi Link Retreiver"
	tableKey    = "hit"
	urlBase = "https://hitomi.la/"

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	tableName = "HentaiItems"

	def loadFeed(self, pageOverride=None):
		self.log.info("Retreiving feed content...",)
		if not pageOverride:
			pageOverride = 1
		try:

			urlPath = '/index-all-{num}.html'.format(num=pageOverride)
			sourceUrl = urllib.parse.urljoin(self.urlBase, urlPath)

			page = self.wg.getSoup(sourceUrl)
		except urllib.error.URLError:
			self.log.critical("Could not get page from Hitomi!")
			self.log.critical(traceback.format_exc())
			return ""

		return page



	def parseLinkDiv(self, linkdiv):

		if not linkdiv.h1:
			return

		date = linkdiv.find("p", class_="date")
		if not date:
			return

		ret = {}

		for row in linkdiv.find_all("tr"):
			if not len(row("td")) == 2:
				continue
			param, val = row("td")
			param = param.get_text().strip()
			val   = val.get_text().strip()


			if param.lower() == "language":

				# Only scrape english TLs and japanese language content.
				# This'll probably miss some other non-japanese content,
				# but they don't seem to have a "translated" tag.
				if val.lower() not in ['english']:
					self.log.info("Skipping item due to language being %s.", val)
					return None

			if param.lower() == "type":
				ret['seriesName']  = val.title()

			# Judge me
			if param.lower() == "tags":
				if "males only" in val.lower() and not "females only" in val.lower():
					self.log.info("Skipping item due to tag 'males only' (%s).", val.replace("\n", " "))
					return None

		ret["originName"] = linkdiv.h1.get_text().strip()
		ret["sourceUrl"] = urllib.parse.urljoin(self.urlBase, linkdiv.h1.a["href"])


		pdate = parser.parse(date.get_text())
		ret["retreivalTime"] = calendar.timegm(pdate.utctimetuple())

		return ret

	def getFeed(self, pageOverride=[None]):
		# for item in items:
		# 	self.log.info(item)
		#

		# self.wg.stepThroughCloudFlare("https://hitomi.la/", titleContains="Hitomi.la")

		ret = []

		for x in pageOverride:
			soup = self.loadFeed(x)


			mainSection = soup.find("div", class_="gallery-content")

			doujinLink = mainSection.find_all("div", class_=re.compile("(cg|dj|manga|acg)"), recursive=False)

			for linkLi in doujinLink:
				tmp = self.parseLinkDiv(linkLi)
				if tmp:
					ret.append(tmp)

		return ret




if __name__ == "__main__":
	import utilities.testBase as tb

	with tb.testSetup(load=False):

		run = DbLoader()
		# dat = run.getFeed(pageOverride=[1])
		# run.go()
		for x in range(13500):
			dat = run.getFeed(pageOverride=[x])
			run.processLinksIntoDB(dat)

