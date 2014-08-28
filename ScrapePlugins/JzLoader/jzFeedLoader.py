
import webFunctions
import bs4
import re

import urllib.parse
import time
import dateutil.parser
import runStatus
import settings
import datetime

import ScrapePlugins.RetreivalDbBase
import nameTools as nt

class JzFeedLoader(ScrapePlugins.RetreivalDbBase.ScraperDbBase):



	loggerPath = "Main.Jz.Fl"
	pluginName = "Japanzai Link Retreiver"
	tableKey = "jz"
	dbName = settings.dbName

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
		soup = bs4.BeautifulSoup(itemPage)

		linkLis = soup.find_all("li", class_="file")

		ret = []

		for linkLi in linkLis:

			item = {}
			dlUrl = urllib.parse.urljoin(seriesUrl, self.quoteUrl(linkLi.a["href"]))
			item["date"]     = time.time()
			item["dlName"]   = linkLi.a.get_text().rsplit("-")[0].strip()
			item["dlLink"]   = dlUrl
			item["baseName"] = seriesName

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
		soup = bs4.BeautifulSoup(basePage)

		seriesPages = self.getSeriesPages(soup, self.urlBase)

		while len(seriesPages):
			seriesName, seriesUrl = seriesPages.pop()

			newDirs, newItems = self.getItemsFromContainer(seriesName, seriesUrl)

			for newDir in newDirs:
				seriesPages.append(newDir)

			for newItem in newItems:
				ret.append(newItem)

		return ret




	def processLinksIntoDB(self, linksDicts, isPicked=False):

		self.log.info( "Inserting...",)
		newItems = 0
		for link in linksDicts:
			if link is None:
				print("linksDicts", linksDicts)
				print("WAT")

			row = self.getRowsByValue(sourceUrl=link["dlLink"])
			if not row:
				newItems += 1
				# Flags has to be an empty string, because the DB is annoying.
				#
				# TL;DR, comparing with LIKE in a column that has NULLs in it is somewhat broken.
				#
				flagStr = ""
				if isPicked:
					flagStr = "picked"



				# Patch series name.
				seriesName = nt.getCanonicalMangaUpdatesName(link["baseName"])

				self.insertIntoDb(retreivalTime = link["date"],
									sourceUrl   = link["dlLink"],
									originName  = link["dlName"],
									dlState     = 0,
									seriesName  = seriesName,
									flags       = flagStr)


				self.log.info("New item: %s", (link["date"], link["dlLink"], link["baseName"], link["dlName"]))


			else:
				row = row.pop()
				if isPicked and not "picked" in row["flags"]:  # Set the picked flag if it's not already there, and we have the item already
					self.updateDbEntry(link["dlLink"], flags=" ".join([row["flags"], "picked"]))


		self.log.info( "Done")
		self.log.info( "Committing...",)
		self.conn.commit()
		self.log.info( "Committed")

		return newItems


	def go(self):

		self.resetStuckItems()
		self.log.info("Getting feed items")

		feedItems = self.getMainItems()
		self.log.info("Processing feed Items")

		self.processLinksIntoDB(feedItems)
		self.log.info("Complete")


