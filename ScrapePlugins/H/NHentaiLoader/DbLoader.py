
import webFunctions

import traceback

import settings
import parsedatetime
import urllib.parse
import time
import calendar
import dateutil.parser

import concurrent.futures
import ScrapePlugins.LoaderBase
class DbLoader(ScrapePlugins.LoaderBase.LoaderBase):


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

		ulDate = dateutil.parser.parse(timeTag['datetime'])
		ultime = ulDate.timestamp()

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


	def parseItem(self, containerDiv, retag=False):
		ret = {}
		ret['sourceUrl'] = urllib.parse.urljoin(self.urlBase, containerDiv.a["href"])

		# Do not decend into items where we've already added the item to the DB
		row = self.getRowsByValue(sourceUrl=ret['sourceUrl'])
		if len(row) and not retag:
			return None

		ret.update(self.getInfo(ret['sourceUrl']))

		# Yaoi isn't something I'm that in to.
		if "guys-only" in ret["tags"] or "males-only" in ret['tags']:
			self.log.info("Yaoi item. Skipping.")
			return None

		titleTd = containerDiv.find("div", class_='caption')
		ret['originName'] = titleTd.get_text().strip()

		return ret


	def update_tags(self, items):
		self.log.info("Doing tag update")
		for item in items:
			rowd = self.getRowsByValue(sourceUrl=item['sourceUrl'])
			if rowd:
				self.log.info("Updating tags for %s", item['sourceUrl'])
				self.addTags(sourceUrl=item['sourceUrl'], tags=item['tags'])

	def getFeed(self, pageOverride=None, retag=False):
		# for item in items:
		# 	self.log.info(item)
		#

		soup = self.loadFeed(pageOverride)

		mainDiv = soup.find("div", class_="index-container")

		divs = mainDiv.find_all("div", class_='gallery')

		ret = []
		for itemDiv in divs:

			item = self.parseItem(itemDiv, retag)
			if item:
				ret.append(item)

		if retag:
			self.update_tags(ret)

		return ret


def process(runner, pageOverride, retag=False):
	print("Executing with page offset: pageOverride")
	res = runner.getFeed(pageOverride=pageOverride, retag=retag)
	print("Received %s results!" % len(res))
	runner._processLinksIntoDB(res)



def getHistory(retag=False):


	print("Getting history")
	run = DbLoader()
	with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
		futures = [executor.submit(process, runner=run, pageOverride=x, retag=retag) for x in range(0, 1500)]
		print("Waiting for executor to finish.")
		executor.shutdown()



	for x in range(0, 1500):
		dat = run.getFeed(pageOverride=x, retag=True)
		run._processLinksIntoDB(dat)


if __name__ == "__main__":
	import utilities.testBase as tb

	with tb.testSetup():
		getHistory(retag=True)
		# run = DbLoader()
		# run.go()


