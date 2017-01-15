import webFunctions

import calendar
import traceback

import bs4
import settings
import dateutil.parser
import datetime
import urllib.parse
import time
import calendar

import ScrapePlugins.RetreivalDbBase
class FakkuFeedLoader(ScrapePlugins.RetreivalDbBase.ScraperDbBase):


	dbName = settings.DATABASE_DB_NAME
	loggerPath = "Main.Manga.Fakku.Fl"
	pluginName = "Fakku Link Retreiver"
	tableKey    = "fk"
	urlBase = "http://www.fakku.net/"

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	tableName = "HentaiItems"

	def parseDateStr(self, inStr):

		# For strings like "n Days Ago", split out the "n", convert it to an int, and take the
		# time-delta so we know what actual date it refers to.

		# convert instances of "a minute ago" to "1 minute ago", for mins, hours, etc...
		inStr = inStr.strip()
		if inStr.lower().startswith("an"):
			inStr = "1"+inStr[2:]

		if inStr.lower().startswith("a"):
			inStr = "1"+inStr[1:]

		if "just now" in inStr:
			updateDate = datetime.datetime.now()
		elif "years ago" in inStr or "year ago" in inStr:
			yearsAgo = inStr.split()[0]
			yearsAgo = int(yearsAgo)
			updateDate = datetime.datetime.now() - datetime.timedelta(yearsAgo*365)
		elif "months ago" in inStr or "month ago" in inStr:
			monthsAgo = inStr.split()[0]
			monthsAgo = int(monthsAgo)
			updateDate = datetime.datetime.now() - datetime.timedelta(monthsAgo*32)
		elif "weeks ago" in inStr or "week ago" in inStr:
			weeksAgo = inStr.split()[0]
			weeksAgo = int(weeksAgo)
			updateDate = datetime.datetime.now() - datetime.timedelta(weeksAgo*7)
		elif "days ago" in inStr or "day ago" in inStr:
			daysAgo = inStr.split()[0]
			daysAgo = int(daysAgo)
			updateDate = datetime.datetime.now() - datetime.timedelta(daysAgo)
		elif "hours ago" in inStr or "hour ago" in inStr:
			hoursAgo = inStr.split()[0]
			hoursAgo = int(hoursAgo)
			updateDate = datetime.datetime.now() - datetime.timedelta(0, hoursAgo*60*60)
		elif "minutes ago" in inStr or "minute ago" in inStr:
			minutesAgo = inStr.split()[0]
			minutesAgo = int(minutesAgo)
			updateDate = datetime.datetime.now() - datetime.timedelta(0, minutesAgo*60)
		elif "seconds ago" in inStr or "second ago" in inStr:
			secondsAgo = inStr.split()[0]
			secondsAgo = int(secondsAgo)
			updateDate = datetime.datetime.now() - datetime.timedelta(0, secondsAgo)
		else:
			self.log.warning("Date parsing failed. Using fall-back parser")
			updateDate = dateutil.parser.parse(inStr, fuzzy=True)
			self.log.warning("Failing string = '%s'", inStr)
			self.log.warning("As parsed = '%s'", updateDate)

		return updateDate


	def extractLinksFromContainer(self, soup, key):

		container = soup.find(text=key)

		if not container:
			self.log.warning("Could not find item containing text '%s'?", key)
			# self.log.warning("Searching in soup '%s'.", soup)
			return []

		items = []
		containerDiv = container.find_parent("div", class_='row')

		tagTags = containerDiv.find_all("a")

		for tagTag in tagTags:
			tagStr = tagTag.get_text()
			tagStr = tagStr.strip()
			tagStr = tagStr.replace(":", " ") # Nuke colon literals (they break the tsvector index)
			while "  " in tagStr:
				tagStr = tagStr.replace("  ", " ")
			tagStr = tagStr.replace(" ", "-")
			if tagStr == "...":
				continue
			items.append(tagStr)

		return items

	def extractTags(self, soup):

		tags = []


		tags = self.extractLinksFromContainer(soup, 'Tags')
		parody = self.extractLinksFromContainer(soup, 'Series')
		artists = self.extractLinksFromContainer(soup, 'Artist')

		for item in parody:
			tags.append(item)
		for item in artists:
			tags.append("artist-"+item)


		tags = ' '.join(tags)
		tags = tags.lower()
		return tags


	def extractNote(self, soup):

		noteHeader = soup.find(text='Description')
		if not noteHeader:
			return ""
		note = noteHeader.parent.next_sibling
		note = note.strip()
		if note == "No description has been written.":
			note = ""

		return note


	def parseDoujinDiv(self, containerDiv):
		ret = {}

		# Put your fucking pay-content somewhere else.
		payola = containerDiv.find('div', class_='fakku-books')
		if payola:
			return False

		# print("Parsing div:", containerDiv)
		# Extract title
		titleLink = containerDiv.find("a", class_='content-title')
		ret["dlName"] = titleLink.get_text()

		# Extract upload date
		dateDiv = containerDiv.find("a", class_='content-time')

		intraTag = dateDiv.find('span', class_='show-mobile')
		if intraTag:
			intraTag.decompose()
		dateStr = dateDiv.get_text()

		if 'Pre-Order Book' in dateStr:
			return None
		if 'Now Available' in dateStr:
			return None

		addDate = self.parseDateStr(dateStr)
		ret["date"] = calendar.timegm(addDate.timetuple())

		# URL
		ret["pageUrl"] = urllib.parse.urljoin(self.urlBase, titleLink["href"])


		ret['tags'] = self.extractTags(containerDiv)
		ret['note'] = self.extractNote(containerDiv)


		series = containerDiv["class"]
		if 'content-row' in series:
			series.remove('content-row')
		if len(series) != 2:
			print(ret["dlName"])
			print(series)
			raise ValueError("Too many div classes!")

		ret['seriesName'] = series[0].title()

		return ret


	def loadFeed(self, pageOverride=None):
		self.log.info("Retreiving feed content...",)
		if not pageOverride:
			pageOverride = 1
		try:
			if pageOverride == 0:
				raise ValueError("Fakku pages start at 1")
			urlPath = '/page/{page}'.format(page=pageOverride)
			pageUrl = urllib.parse.urljoin(self.urlBase, urlPath)
			print("Fetching page at", pageUrl)
			page = self.wg.getpage(pageUrl)
		except urllib.error.URLError:
			self.log.critical("Could not get page from Fakku!")
			self.log.critical(traceback.format_exc())
			return ""

		return page


	def getItems(self, pageOverride=None):
		# for item in items:
		# 	self.log.info(item)
		#

		page = self.loadFeed(pageOverride)
		soup = bs4.BeautifulSoup(page, "lxml")

		mainSection = soup.find("div", id="content")
		doujinDiv = mainSection.find_all("div", class_="content-row")

		ret = []
		for linkLi in doujinDiv:
			item = self.parseDoujinDiv(linkLi)

			if not item:
				self.log.info("Skipping item, because it's pay-content.")
				continue

			for skipTag in settings.skipTags:
				if skipTag in item['tags']:
					self.log.info("Skipped tag '%s' in tags '%s'. Do not want.", skipTag, item['tags'])
					continue

			ret.append(self.parseDoujinDiv(linkLi))

		return ret


	def processLinksIntoDB(self, linksDict):
		self.log.info("Inserting...")

		newItemCount = 0

		for link in linksDict:

			row = self.getRowsByValue(sourceUrl=link["pageUrl"])
			if not row:
				curTime = time.time()
				self.insertIntoDb(retreivalTime = link["date"],
									sourceUrl   = link["pageUrl"],
									originName  = link["dlName"],
									seriesName  = link["seriesName"],
									tags        = link["tags"],
									note        = link["dlName"],
									dlState     = 0)
				# cur.execute('INSERT INTO fufufuu VALUES(?, ?, ?, "", ?, ?, "", ?);',(link["date"], 0, 0, link["dlLink"], link["itemTags"], link["dlName"]))
				self.log.info("New item: %s", (curTime, link["pageUrl"], link["dlName"]))

			else:
				self.addTags(sourceUrl=link["pageUrl"], tags=link['tags'])

		self.log.info("Done")
		self.log.info("Committing...",)
		self.conn.commit()
		self.log.info("Committed")

		return newItemCount


	def go(self):
		self.resetStuckItems()
		dat = self.getItems()
		self.processLinksIntoDB(dat)

	def goHistory(self):

		for x in range(0, 125):
			dat = self.getItems(pageOverride=x)
			self.processLinksIntoDB(dat)


if __name__ == "__main__":
	import utilities.testBase as tb

	with tb.testSetup(startObservers=False):
		# getHistory()
		run = FakkuFeedLoader()
		# run.getFeed()
		# run.go()
		run.goHistory()
