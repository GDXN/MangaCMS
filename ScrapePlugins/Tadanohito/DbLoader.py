
import webFunctions

import calendar
import traceback

import settings
import bs4
import re
import dateutil.parser
import copy
import urllib.parse
import time
import calendar

import ScrapePlugins.RetreivalDbBase
class DbLoader(ScrapePlugins.RetreivalDbBase.ScraperDbBase):


	dbName = settings.DATABASE_DB_NAME
	loggerPath = "Main.Manga.Tadanohito.Fl"
	pluginName = "Tadanohito Link Retreiver"
	tableKey    = "ta"
	urlBase = "http://www.tadanohito.net"
	urlFeed = "http://www.tadanohito.net/rss_news.php"

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	tableName = "HentaiItems"



	# -----------------------------------------------------------------------------------
	# Login Management tools
	# -----------------------------------------------------------------------------------


	def checkLogin(self):

		getPage = self.wg.getpage(r"http://www.tadanohito.net/news.php")
		if "Welcome, {username}".format(username=settings.tadanohito["login"]) in getPage:
			self.log.info("Still logged in")
			return
		else:
			self.log.info("Whoops, need to get Login cookie")

		logondict = {
			"user_name"   : settings.tadanohito["login"],
			"user_pass"   : settings.tadanohito["passWd"],
			"remember_me" : "y",
			"login"       : "Login"
			}


		getPage = self.wg.getpage(r"http://www.tadanohito.net/news.php", postData=logondict)
		if "Welcome, {username}".format(username=settings.tadanohito["login"]) in getPage:
			self.log.info("Logged in successfully!")
		elif "You are now logged in as:" in getPage:
			self.log.error("Login failed!")

		self.wg.saveCookies()



	# -----------------------------------------------------------------------------------
	# The scraping parts
	# -----------------------------------------------------------------------------------





	def getUploadTime(self, dateStr):
		# ParseDatetime COMPLETELY falls over on "YYYY-MM-DD HH:MM" formatted strings. Not sure why.
		# Anyways, dateutil.parser.parse seems to work ok, so use that.
		updateDate = dateutil.parser.parse(dateStr)
		ret = calendar.timegm(updateDate.timetuple())

		# Patch times for the local-GMT offset.
		# using `calendar.timegm(time.gmtime()) - time.time()` is NOT ideal, but it's accurate
		# to a second or two, and that's all I care about.
		gmTimeOffset = calendar.timegm(time.gmtime()) - time.time()
		ret = ret - gmTimeOffset
		return ret



	def getFeed(self):
		# for item in items:
		# 	self.log.info(item)
		#

		ret = []

		soup = self.wg.getSoup(self.urlFeed)

		entries = soup.find_all("item")


		for entry in entries:
			ds = entry.pubdate.get_text()
			ulDate = self.getUploadTime(ds)
			desc = entry.description.get_text()
			dSoup = bs4.BeautifulSoup(desc)
			for link in dSoup.find_all("a"):
				if 'http://www.tadanohito.net/infusions/pro_download_panel/download.php?did=' in link['href']:

					item = {
						'retreivalTime' : ulDate,
						'sourceUrl'     : link['href']
					}
					ret.append(item)
			# item = self.parseItem(row)
			# if item:
			# 	ret.append(item)


		return ret


	def go(self):
		self.resetStuckItems()
		self.checkLogin()

		dat = self.getFeed()

		self.processLinksIntoDB(dat)


# Base url for items?
# http://www.tadanohito.net/infusions/pro_download_panel/download.php

if __name__ == "__main__":
	import utilities.testBase as tb

	with tb.testSetup(startObservers=False):
		# login()
		run = DbLoader()
		# run.checkLogin()
		run.go()
		# run.getFeed()


