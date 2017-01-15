
import webFunctions

import calendar
import traceback

import settings
import parsedatetime
import urllib.parse
import time
import calendar

import ScrapePlugins.RetreivalDbBase
class DbLoader(ScrapePlugins.RetreivalDbBase.ScraperDbBase):


	dbName = settings.DATABASE_DB_NAME
	loggerPath = "Main.Manga.NHentai.Fl"
	pluginName = "NHentai Link Retreiver"
	tableKey    = "nh"
	urlBase = "http://nhentai.net/"
	urlFeed = "http://nhentai.net/language/english/?page={num}"

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	tableName = "HentaiItems"

	def loadFeed(self, pageOverride=None):
		self.log.info("Retreiving feed content...",)
		if not pageOverride:
			pageOverride = 1
		try:
			pageUrl = self.urlFeed.format(num=pageOverride)
			soup = self.wg.getSoup(pageUrl)
		except urllib.error.URLError:
			self.log.critical("Could not get page from NHentai!")
			self.log.critical(traceback.format_exc())
			return None

		return soup


	def getCategoryTags(self, soup):
		tagChunks = soup.find_all('div', class_='field-name')
		tags = []
		category = "None"



		# 'Origin'       : '',  (Category)
		for chunk in tagChunks:
			for rawTag in chunk.find_all("a", class_='tag'):
				if rawTag.span:
					rawTag.span.decompose()
				tag = rawTag.get_text().strip()

				if "Artist" in chunk.contents[0]:
					category = "Artist-"+tag.title()
					tag = "artist "+tag
				tag = tag.replace("  ", " ")
				tag = tag.replace(" ", "-")
				tags.append(tag)

		tags = " ".join(tags)
		return category, tags

	def getUploadTime(self, soup):
		timeTag = soup.find("time")
		if not timeTag:
			raise ValueError("No time tag found!")

		cal = parsedatetime.Calendar()
		ulDate, status = cal.parse(timeTag['datetime'])
		# print(ulDate)
		ultime = calendar.timegm(ulDate)

		# No future times!
		if ultime > time.time():
			self.log.warning("Clamping timestamp to now!")
			ultime = time.time()
		return ultime


	def getInfo(self, itemUrl):
		ret = {}
		soup = self.wg.getSoup(itemUrl)

		ret["seriesName"], ret['tags'] = self.getCategoryTags(soup)
		ret['retreivalTime'] = self.getUploadTime(soup)

		return ret


	def parseItem(self, containerDiv):
		ret = {}
		ret['sourceUrl'] = urllib.parse.urljoin(self.urlBase, containerDiv.a["href"])

		# Do not decend into items where we've already added the item to the DB
		if len(self.getRowsByValue(sourceUrl=ret['sourceUrl'])):
			return None

		ret.update(self.getInfo(ret['sourceUrl']))

		# Yaoi isn't something I'm that in to.
		if "guys-only" in ret["tags"] or "males-only" in ret['tags']:
			self.log.info("Yaoi item. Skipping.")
			return None

		titleTd = containerDiv.find("div", class_='caption')
		ret['originName'] = titleTd.get_text().strip()

		return ret

	def getFeed(self, pageOverride=None):
		# for item in items:
		# 	self.log.info(item)
		#

		soup = self.loadFeed(pageOverride)

		mainDiv = soup.find("div", class_="index-container")

		divs = mainDiv.find_all("div", class_='gallery')

		ret = []
		for itemDiv in divs:

			item = self.parseItem(itemDiv)
			if item:
				ret.append(item)


		return ret

	def go(self):
		self.resetStuckItems()
		dat = self.getFeed()


		self.processLinksIntoDB(dat)

		# for x in range(10):
		# 	dat = self.getFeed(pageOverride=x)
		# 	self.processLinksIntoDB(dat)



def getHistory():

	run = DbLoader()
	# dat = run.getFeed()
	# print(dat)
	for x in range(0, 1500):
		dat = run.getFeed(pageOverride=x)
		run.processLinksIntoDB(dat)


if __name__ == "__main__":
	import utilities.testBase as tb

	with tb.testSetup(startObservers=False):
		getHistory()
		# run = DbLoader()
		# run.go()


