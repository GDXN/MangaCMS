
import webFunctions
import bs4
import re

import urllib.parse
import time
import dateutil.parser
import runStatus
import settings
import datetime
import traceback

import ScrapePlugins.RetreivalDbBase
import nameTools as nt

class JzFeedLoader(ScrapePlugins.RetreivalDbBase.ScraperDbBase):



	loggerPath = "Main.Manga.Jz.Fl"
	pluginName = "Japanzai Link Retreiver"
	tableKey = "jz"
	dbName = settings.DATABASE_DB_NAME

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	urlBase = "http://download.japanzai.com/"

	tableName = "MangaItems"

	def checkLogin(self):
		pass

	def closeDB(self):
		self.log.info( "Closing DB...",)
		self.conn.close()
		self.log.info( "done")

	def quoteUrl(self, url):
		# print("InUrl = '%s'" % url)
		scheme, netloc, path, params, query, fragment = urllib.parse.urlparse(url)
		# print((scheme, netloc, path, params, query, fragment))
		path     = urllib.parse.quote(path)
		params   = urllib.parse.quote(params)
		query    = urllib.parse.quote(query, safe="/=")
		fragment = urllib.parse.quote(fragment)
		# print((scheme, netloc, path, params, query, fragment))
		url = urllib.parse.urlunparse((scheme, netloc, path, params, query, fragment))
		# print("outUrl = '%s'" % url)
		return url

	def getItemsFromContainer(self, seriesName, seriesUrl):
		self.log.info("Fetching items for series '%s'", seriesName)


		self.log.info("Using URL '%s'", seriesUrl)
		itemPage = self.wg.getpage(seriesUrl)
		soup = bs4.BeautifulSoup(itemPage, "lxml")

		linkLis = soup.find_all("li", class_="file")

		ret = []

		for linkLi in linkLis:

			item = {}
			dlUrl = urllib.parse.urljoin(seriesUrl, self.quoteUrl(linkLi.a["href"]))
			item["retreivalTime"]     = time.time()
			item["originName"]   = linkLi.a.get_text().rsplit("-")[0].strip()
			item["sourceUrl"]   = dlUrl
			item["seriesName"] = seriesName

			ret.append(item)


		moreDirs = self.getSeriesPages(soup, seriesUrl)

		return moreDirs, ret



	def getSeriesPages(self, soup, urlBase):

		linkLis = soup.find_all("li", class_="directory")

		ret = []
		for linkLi in linkLis:
			series = linkLi.a.get_text()
			if series == "..":
				continue
			url = urllib.parse.urljoin(urlBase, self.quoteUrl(linkLi.a["href"]))
			ret.append((series, url))

			if not runStatus.run:
				self.log.info("Breaking due to exit flag being set")
				return

		return ret

	def getMainItems(self):
		# for item in items:
		# 	self.log.info( item)
		#

		self.log.info( "Loading Japanzai Main Feed")

		ret = []

		basePage = self.wg.getpage(self.urlBase)
		soup = bs4.BeautifulSoup(basePage, "lxml")

		seriesPages = self.getSeriesPages(soup, self.urlBase)

		while len(seriesPages):
			seriesName, seriesUrl = seriesPages.pop()

			try:
				newDirs, newItems = self.getItemsFromContainer(seriesName, seriesUrl)

				for newDir in newDirs:
					seriesPages.append(newDir)

				for newItem in newItems:
					ret.append(newItem)
			except urllib.error.URLError:
				self.log.error("Failed to retreive page at url '%s'", seriesUrl)
				self.log.error(traceback.format_exc())


		return ret




	def go(self):

		self.resetStuckItems()
		self.log.info("Getting feed items")

		feedItems = self.getMainItems()
		self.log.info("Processing feed Items")

		self.processLinksIntoDB(feedItems)
		self.log.info("Complete")


