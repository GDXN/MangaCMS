
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
import calendar

import ScrapePlugins.RetreivalDbBase
class HBrowseDbLoader(ScrapePlugins.RetreivalDbBase.ScraperDbBase):


	dbName = settings.DATABASE_DB_NAME
	loggerPath = "Main.Manga.HBrowse.Fl"
	pluginName = "H-Browse Link Retreiver"
	tableKey    = "hb"
	urlBase = "http://www.hbrowse.com/"
	urlFeed = "http://www.hbrowse.com/list"

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	tableName = "HentaiItems"

	def loadFeed(self, pageOverride=None):
		self.log.info("Retreiving feed content...",)
		if not pageOverride:
			pageOverride = 1
		try:
			# I really don't get the logic behind HBrowse's path scheme.
			urlPath = '/list/{num}'.format(num=pageOverride)
			pageUrl = urllib.parse.urljoin(self.urlBase, urlPath)

			page = self.wg.getpage(pageUrl)
		except urllib.error.URLError:
			self.log.critical("Could not get page from HBrowse!")
			self.log.critical(traceback.format_exc())
			return ""

		return page



	def parseItem(self, row, timestamp):
		ret = {}
		ret['retreivalTime'] = timestamp
		ret['sourceUrl'] = urllib.parse.urljoin(self.urlBase, row.a["href"])
		titleTd = row.find("td", class_='recentTitle')
		ret['originName'] = titleTd.get_text()



		return ret

	def extractDate(self, row):
		text = row.get_text()
		date = parser.parse(text)
		timestamp = calendar.timegm(date.timetuple())
		return timestamp

	def getFeed(self, pageOverride=None):
		# for item in items:
		# 	self.log.info(item)
		#

		page = self.loadFeed(pageOverride)

		soup = bs4.BeautifulSoup(page, "lxml")

		itemTable = soup.find("table", id="recentTable")

		rows = itemTable.find_all("tr")

		ret = []
		for row in rows:

			if row.find("td", class_='recentDate'):
				curTimestamp = self.extractDate(row)

			elif row.find("td", class_='recentTitle'):
				# curTimestamp is specifically not pre-defined, because I want to fail noisily if I try
				# to parse a link row before seeing a valid date
				item = self.parseItem(row, curTimestamp)

				if 'originName' in item:
					# If cloudflare is fucking shit up, just try to get the title from the title tag.
					if r"[email\xa0protected]" in item['originName'] or r'[email protected]' in item['originName']:
						item['originName'] = soup.title.get_text().split(" by ")[0]
				else:
					item['originName'] = soup.title.get_text().split(" by ")[0]

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

	run = HBrowseDbLoader()
	for x in range(400):
		dat = run.getFeed(pageOverride=x)
		run.processLinksIntoDB(dat)


if __name__ == "__main__":
	import utilities.testBase as tb

	with tb.testSetup(startObservers=False):
		getHistory()
		run = HBrowseDbLoader()
		run.go()

