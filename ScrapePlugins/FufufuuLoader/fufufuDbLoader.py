import webFunctions
import settings

import time
import traceback
import bs4
import urllib.parse
import logging

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait # available since 2.4.0
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

import http.cookiejar


import ScrapePlugins.RetreivalDbBase
class FuFuFuuDbLoader(ScrapePlugins.RetreivalDbBase.ScraperDbBase):
	log = logging.getLogger("Main.Fu.Fl")


	wg = webFunctions.WebGetRobust()

	loggerPath = "Main.Fu.Fl"
	pluginName = "Fufufu Link Retreiver"
	tableKey    = "fu"
	dbName = settings.dbName
	urlBase = "http://fufufuu.net/"


	def checkThruCloudFlare(self):
		self.log.info("Stepping through possible cloudflare protection.")

		dcap = dict(DesiredCapabilities.PHANTOMJS)
		wgSettings = dict(self.wg.browserHeaders)
		dcap["phantomjs.page.settings.userAgent"] = wgSettings['User-Agent']

		if "Accept-Language" in wgSettings:
			dcap['phantomjs.page.customHeaders.Accept-Language'] = wgSettings['Accept-Language']

		if 'Accept-Charset' in wgSettings:
			dcap['phantomjs.page.customHeaders.Accept-Charset'] = wgSettings['Accept-Charset']
		# profile.set_preference("general.useragent.override", "some UA string")

		dcap['phantomjs.cli.args'] = '--cookies-file=phantomCookies.txt'

		self.driver = webdriver.PhantomJS(desired_capabilities=dcap)
		self.driver.set_window_size(1024, 768)

		cookieAttrs = ['name', 'value', 'path', 'domain', 'secure', 'expiry']


		# for cookie in self.wg.cj:
		# 	print cookie
		# 	newCookie = {}
		# 	for attr in cookieAttrs:
		# 		if hasattr(cookie, attr):
		# 			attrVal = getattr(cookie, attr)
		# 			if attrVal:
		# 				newCookie[attr] = attrVal

		# 	print newCookie
			# self.driver.add_cookie(newCookie)

		# raise ValueError

		self.driver.get(self.urlBase)

		try:
			WebDriverWait(self.driver, 20).until(EC.title_contains(("Fufufuu")))
			success = True
		except TimeoutException:
			self.log.error("Could not pass through cloudflare blocking!")
			success = False
		# Add cookies to cookiejar
		for cookie in self.driver.get_cookies():
			self.wg.addSeleniumCookie(cookie)
			#print cookie[u"value"]

		self.wg.syncCookiesFromFile()
		self.log.info("Have session cookies")

		return success


	def go(self):
		self.log.info("Checking Fufufuu feeds for updates")
		#print "lawl", fl

		self.checkThruCloudFlare()
		dat = self.getFeed()
		self.processLinksIntoDB(dat)



	def loadFeed(self, pageOverride=None):
		if not pageOverride:
			pageOverride = 1
		targetURL = urllib.parse.urljoin(self.urlBase, "?p=%d" % pageOverride)
		self.log.info("Retreiving feed content for url: %s", targetURL)
		self.driver.get(targetURL)
		feed = self.driver.page_source
		soup = bs4.BeautifulSoup(feed)
		self.log.info("done")
		return soup

	def _checkIfWantItem(self, tags, item):
		for tag in tags:
			tag = tag.rstrip().lstrip()
			if "Yaoi".lower() in tag.lower():
				self.log.info("Yaoi. Skipping %s", item)
				return False
			if "한국어".lower() in tag.lower():
				self.log.info("Korean language. Skipping %s", item)
				return False
			if "日本語".lower() in tag.lower():
				self.log.info("Japanese Language. Skipping %s", item)
				return False
		return True

	def getFeed(self, pageOverride=None):
		# for item in items:
		# 	self.log.info(item)
		#

		self.resetStuckItems()

		feed = self.loadFeed(pageOverride)
		items = feed.find_all("li", class_="mli")
		ret = []
		for feedEntry in items:
			item = {}
			# print feedEntry
			try:
				item["dlName"] = feedEntry.find("a", class_="mli-title").text
				item["dlLink"] = urllib.parse.urljoin(self.urlBase, feedEntry.a["href"])
				tags = []
				for tag in feedEntry.find("div", class_="mli-info"):
					tags.append(tag.get_text().rstrip().lstrip().replace(" ", "-"))

				item["itemTags"] = ' '.join(tags)
				item["date"] = time.time()
				#self.log.info("date = ", feedEntry['published_parsed'])


				# print item
				#self.log.info(item)
				if self._checkIfWantItem(tags, item):
					ret.append(item)

			except:
				self.log.info("WAT?")
				traceback.print_exc()

		return ret



	def processLinksIntoDB(self, linksDict):
		cur = self.conn.cursor()
		self.log.info("Inserting...",)

		for link in linksDict:

			row = self.getRowsByValue(sourceUrl=link["dlLink"])
			if not row:
				self.insertIntoDb(retreivalTime=link["date"], sourceUrl=link["dlLink"], tags=link["itemTags"], originName=link["dlName"], dlState=0)
				# cur.execute('INSERT INTO fufufuu VALUES(?, ?, ?, "", ?, ?, "", ?);',(link["date"], 0, 0, link["dlLink"], link["itemTags"], link["dlName"]))
				self.log.info("New item: %s", (link["date"], link["dlLink"], link["dlName"], link["itemTags"]))

		self.log.info("Done")
		self.log.info("Committing...",)
		self.conn.commit()
		self.log.info("Committed")
