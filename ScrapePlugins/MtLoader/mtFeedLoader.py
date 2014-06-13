
import feedparser
import webFunctions
import bs4
import re
import nameTools as nt
import urllib.parse
import time
import datetime
from dateutil import parser
import settings
import calendar

import ScrapePlugins.RetreivalDbBase

class MtFeedLoader(ScrapePlugins.RetreivalDbBase.ScraperDbBase):



	wg = webFunctions.WebGetRobust()
	loggerPath = "Main.Mt.Fl"
	pluginName = "MangaTraders Link Retreiver"
	tableName = "MangaItems"
	dbName = settings.dbName
	urlBase = "http://www.mangatraders.com/"

	watchedItemURL = "http://www.mangatraders.com/profile/%s/watched" % settings.mtSettings["watchedFeedNo"]
	personalFeedUrl = "http://www.mangatraders.com/rss/watched/%s" % settings.mtSettings["watchedFeedNo"]
	mainFeedUrl = "http://www.mangatraders.com/rss/files/"









	def checkLogin(self):
		for cookie in self.wg.cj:
			if "SMFCookie232" in str(cookie):   # We have a log-in cookie
				return True

		self.log.info( "Getting Login cookie")
		logondict = {"login-user" : settings.mtSettings["login"], "login-pass" : settings.mtSettings["passWd"], "rememberme" : "on"}
		self.wg.getpage('http://www.mangatraders.com/login/processlogin', postData=logondict)

		self.wg.saveCookies()

	def closeDB(self):
		self.log.info( "Closing DB...",)
		self.conn.close()
		self.log.info( "done")

	def loadFeed(self, url):
		self.log.info( "Retreiving feed content...",)
		feed = feedparser.parse( url )
		self.log.info( "done")
		return feed



	def getFeed(self, url):
		# for item in items:
		# 	self.log.info( item)
		#
		self.log.info( "Loading MT Feeds")
		feed = self.loadFeed(url)
		ret = []
		for feedEntry in feed["entries"]:
			item = {}
			#for key, value in feedEntry.iteritems():
			#	self.log.info( key, value)
			#self.log.info( feedEntry["links"][0]["href"])

			dlName = feedEntry["title_detail"]["value"]
			dlLink = feedEntry["links"][0]["href"]
			item["dlName"] = dlName
			item["dlLink"] = dlLink
			item["date"] = time.mktime(feedEntry['published_parsed'])
			#self.log.info( "date = ", feedEntry['published_parsed'])

			nameRe = re.compile(r"<b>Series:</b> <a href=\"http://www.mangatraders.com/manga/series/(\d+)\">(.+?)</a>")

			result = nameRe.search(feedEntry["summary_detail"]["value"])
			if result:
				item["sourceId"] = nt.makeFilenameSafe(result.group(1))
				item["baseName"] = nt.makeFilenameSafe(result.group(2))
			else:
				self.log.warning("Need to manually clean filename. What's going on?")
				tempCleaned = nt.getCleanedName(dlName)

				item["baseName"] = nt.makeFilenameSafe(tempCleaned)
				item["sourceId"] = None

			ret.append(item)

		return ret
	def getPersonalItems(self):
		page = self.wg.getpage(self.watchedItemURL)
		soup = bs4.BeautifulSoup(page)
		ret = []
		for fileBlock in soup.find_all("file"):

			mangaName = fileBlock.cat_disp.string
			cleanedName = nt.makeFilenameSafe(mangaName)
			addDate = calendar.timegm(parser.parse(fileBlock.file_add_date.string).utctimetuple())
			fileName = fileBlock.file_disp.string
			sourceId = fileBlock.file_cat.string
			fileID = fileBlock.fileid.string

			item = {}
			item["date"] = addDate
			item["dlName"] = fileName
			item["dlLink"] =  "http://www.mangatraders.com/download/file/%s" % fileID
			item["baseName"] = cleanedName
			item["sourceId"] = sourceId
			item["dlServer"] = ""
			ret.append(item)

		return ret

	def getMainItems(self, rangeOverride=None, rangeOffset=None):
		# for item in items:
		# 	self.log.info( item)
		#
		urlFormat = "http://www.mangatraders.com/releases/%s/"
		urlBase = "http://www.mangatraders.com/"

		self.log.info( "Loading MT Main Feed")

		ret = []
		if not rangeOverride:
			dayDelta = 3
		else:
			dayDelta = int(rangeOverride)
		if not rangeOffset:
			rangeOffset = 0

		for daysAgo in range(dayDelta):
			day = datetime.date.today() - datetime.timedelta(daysAgo+rangeOffset)
			url = urlFormat % day.strftime("%Y-%m-%d")
			page = self.wg.getpage(url)
			soup = bs4.BeautifulSoup(page)
			dataTable = soup.find("div", id="dataTable")
			for row in dataTable.find_all("tr"):
				rowItems = row.find_all("td")
				if len(rowItems) == 5:
					server, chName, seriesName, size, view = rowItems

					if chName.find("del"):
						self.log.info("Skipping file previously downloaded - %s", chName.a.string)
						continue

					item = {}
					if day == datetime.date.today():
						item["date"] = time.time()
					else:
						item["date"] = time.mktime(day.timetuple())
					item["dlName"] = chName.a.string
					item["dlLink"] =  urllib.parse.urljoin(urlBase, chName.a["href"])
					item["baseName"] = nt.makeFilenameSafe(seriesName.a.string)
					item["sourceId"] = nt.makeFilenameSafe(seriesName.a["href"].split("/")[-1])
					item["dlServer"] = server.img["alt"]
					ret.append(item)
		return ret



	def resetStuckItems(self):
		self.log.info("Resetting stuck downloads in DB")
		self.conn.execute('''UPDATE {table} SET dlState=0 WHERE dlState=1'''.format(table=self.tableName))
		self.conn.commit()
		self.log.info("Download reset complete")


	def processLinksIntoDB(self, linksDicts, isPicked):

		self.log.info( "Inserting...",)
		newItems = 0
		for link in linksDicts:

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

				self.insertIntoDb(retreivalTime=link["date"],
									sourceUrl=link["dlLink"],
									originName=link["dlName"],
									dlState=0,
									seriesName=link["baseName"],
									sourceId=link["sourceId"],
									dlServer=link["dlServer"],
									flags=flagStr)


				# cur.execute('INSERT INTO fufufuu VALUES(?, ?, ?, "", ?, ?, "", ?);',(link["date"], 0, 0, link["dlLink"], link["itemTags"], link["dlName"]))
				self.log.info("New item: %s", (link["date"], link["dlLink"], link["baseName"], link["dlName"]))


			else:
				row = row.pop()
				if isPicked and not "picked" in row["flags"]:  # Set the picked flag if it's not already there, and we have the item already
					self.updateDbEntry(link["dlLink"],flags=" ".join([row["flags"], "picked"]))

				if link["sourceId"] != None and link["sourceId"] != row["sourceId"]:
					# self.log.info("Need to update sourceId - %s:%s", link["baseName"], link["sourceId"])
					self.updateDbEntry(link["dlLink"], sourceId=link["sourceId"])


		self.log.info( "Done")
		self.log.info( "Committing...",)
		self.conn.commit()
		self.log.info( "Committed")

		#for row in cur.execute('SELECT * FROM links'):
		#	self.log.info( row)

		return newItems


	def go(self):
		# HAAACK
		# OVerride column names because *just* the MT table has an extra column
		self.validKwargs = ["dlServer", "dlState", "sourceUrl", "retreivalTime", "lastUpdate", "sourceId", "seriesName", "fileName", "originName", "downloadPath", "flags", "tags", "note"]




		self.resetStuckItems()
		self.log.info( "Getting personal feed")
		items = self.getPersonalItems()
		self.processLinksIntoDB(items, isPicked=1)

		oldFeedItems = self.getMainItems()
		self.log.info( "Processing older main feed")

		self.processLinksIntoDB(oldFeedItems, isPicked=0)

