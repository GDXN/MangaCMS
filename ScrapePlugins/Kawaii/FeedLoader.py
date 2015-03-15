
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

# Only downlad items in language specified.
# Set to None to disable filtering (e.g. fetch ALL THE FILES).
DOWNLOAD_ONLY_LANGUAGE = "English"

class FeedLoader(ScrapePlugins.RetreivalDbBase.ScraperDbBase):



	loggerPath = "Main.Kw.Fl"
	pluginName = "Kawaii-Scans Link Retreiver"
	tableKey = "kw"
	dbName = settings.DATABASE_DB_NAME

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	tableName = "MangaItems"

	urlBase = "http://kawaii.ca/"

	feedUrl = "http://kawaii.ca/reader/"


	def closeDB(self):
		self.log.info( "Closing DB...",)
		self.conn.close()
		self.log.info( "done")


	def getItemPages(self, url, title):
		print("Should get item for ", url)

		soup = self.wg.getSoup(url)
		ret = []

		pager = soup.find("div", class_="pager")
		spans = pager.find_all('span')
		if len(spans) != 3:
			self.log.error("Invalid span items! Page: '%s'", url)
			return ret

		dummy_series, chapter, dummy_page = spans

		# First string in the tag should be "Chapter".
		assert 'Chapter' in list(chapter.stripped_strings)[0]


		for option in chapter.find_all("option"):
			item = {}

			chapUrl = '{series}/{chapter}'.format(series=url, chapter=option['value'])
			chapTitle = option.get_text()


			item["originName"]     = "{series} - {file}".format(series=title, file=chapTitle)
			item["sourceUrl"]      = chapUrl
			item["seriesName"]     = title

			# There is no upload date information
			item["retreivalTime"]  = time.time()


			ret.append(item)

		return ret



	def getSeriesUrls(self):
		ret = []
		print("wat?")
		soup = self.wg.getSoup(self.feedUrl)
		div = soup.find("div", class_="pager")
		for option in div.find_all('option'):
			if option['value'] == '0':
				continue
			url = 'http://kawaii.ca/reader/{manga}'.format(manga=option['value'])
			ret.append((url, option.get_text()))

		return ret

	def getAllItems(self):

		self.log.info( "Loading Mc Items")

		ret = []

		seriesPages = self.getSeriesUrls()


		for url, title in seriesPages:

			itemList = self.getItemPages(url, title)
			for item in itemList:
				ret.append(item)

			if not runStatus.run:
				self.log.info( "Breaking due to exit flag being set")
				break
		self.log.info("Found %s total items", len(ret))
		return ret



	def go(self):

		self.resetStuckItems()
		self.log.info("Getting feed items")

		feedItems = self.getAllItems()
		self.log.info("Processing feed Items")

		self.processLinksIntoDB(feedItems)
		self.log.info("Complete")



if __name__ == "__main__":
	print('wat')

	import utilities.testBase as tb

	with tb.testSetup(startObservers=False):
		cl = FeedLoader()

		cl.go()