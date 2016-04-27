
import webFunctions

import calendar
import traceback

import settings
import re
import parsedatetime
import dateutil.parser
import copy
import urllib.parse
import time
import calendar

import ScrapePlugins.RetreivalDbBase
class DbLoader(ScrapePlugins.RetreivalDbBase.ScraperDbBase):


	dbName = settings.DATABASE_DB_NAME
	loggerPath = "Main.Manga.SadPanda.Fl"
	pluginName = "SadPanda Link Retreiver"
	tableKey    = "sp"
	urlBase = "http://exhentai.org/"
	urlFeed = "http://exhentai.org/?page={num}&f_search={search}"

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	tableName = "HentaiItems"



	# -----------------------------------------------------------------------------------
	# Login Management tools
	# -----------------------------------------------------------------------------------


	def checkLogin(self):

		checkPage = self.wg.getpage(r"https://forums.e-hentai.org/index.php?")
		if "Logged in as" in checkPage:
			self.log.info("Still logged in")
			return
		else:
			self.log.info("Whoops, need to get Login cookie")

		logondict = {
			"UserName"   : settings.sadPanda["login"],
			"PassWord"   : settings.sadPanda["passWd"],
			"referer"    : "https://forums.e-hentai.org/index.php?",
			"CookieDate" : "Log me in",
			"b"          : '',
			"bt"         : '',
			"submit"     : "Log me in"
			}

		getPage = self.wg.getpage(r"https://forums.e-hentai.org/index.php?act=Login&CODE=01", postData=logondict)
		if "Username or password incorrect" in getPage:
			self.log.error("Login failed!")
			with open("pageTemp.html", "wb") as fp:
				fp.write(getPage)
		elif "You are now logged in as:" in getPage:
			self.log.info("Logged in successfully!")

		confdict = {
			'uh'          : 'y',
			'xr'          : 'a',
			'rx'          : '0',
			'ry'          : '0',
			'tl'          : 'r',
			'ar'          : '0',
			'dm'          : 'l',
			'prn'         : 'y',
			'f_doujinshi' : 'on',
			'f_manga'     : 'on',
			'f_artistcg'  : 'on',
			'f_gamecg'    : 'on',
			'f_western'   : 'on',
			'f_non-h'     : 'on',
			'f_imageset'  : 'on',
			'f_cosplay'   : 'on',
			'f_asianporn' : 'on',
			'f_misc'      : 'on',
			'favorite_0'  : 'Favorites+0',
			'favorite_1'  : 'Favorites+1',
			'favorite_2'  : 'Favorites+2',
			'favorite_3'  : 'Favorites+3',
			'favorite_4'  : 'Favorites+4',
			'favorite_5'  : 'Favorites+5',
			'favorite_6'  : 'Favorites+6',
			'favorite_7'  : 'Favorites+7',
			'favorite_8'  : 'Favorites+8',
			'favorite_9'  : 'Favorites+9',
			'xl_1034'     : 'on',
			'xl_1044'     : 'on',
			'xl_1054'     : 'on',
			'xl_1064'     : 'on',
			'xl_1074'     : 'on',
			'xl_1084'     : 'on',
			'xl_1094'     : 'on',
			'xl_1104'     : 'on',
			'xl_1114'     : 'on',
			'xl_1124'     : 'on',
			'xl_1134'     : 'on',
			'xl_1144'     : 'on',
			'xl_1154'     : 'on',
			'xl_1278'     : 'on',
			'xl_1279'     : 'on',
			'xl_2048'     : 'on',
			'xl_2049'     : 'on',
			'xl_2058'     : 'on',
			'xl_2068'     : 'on',
			'xl_2078'     : 'on',
			'xl_2088'     : 'on',
			'xl_2098'     : 'on',
			'xl_2108'     : 'on',
			'xl_2118'     : 'on',
			'xl_2128'     : 'on',
			'xl_2138'     : 'on',
			'xl_2148'     : 'on',
			'xl_2158'     : 'on',
			'xl_2168'     : 'on',
			'xl_2178'     : 'on',
			'xl_2302'     : 'on',
			'xl_2303'     : 'on',
			'fs'          : 'p',
			'ru'          : 'RRGGB',
			'rc'          : '3',
			'lt'          : 'm',
			'ts'          : 'm',
			'tr'          : '2',
			'cs'          : 'a',
			'sc'          : '0',
			'to'          : 'a',
			'pn'          : '0',
			'hp'          : '',
			'hk'          : '',
			'sa'          : 'y',
			'oi'          : 'n',
			'apply'       : 'Apply',
			}
		headers = {
			'Referer': 'http://g.e-hentai.org/uconfig.php',
			'Host': 'g.e-hentai.org'
		}
		getPage = self.wg.getpage(r"http://g.e-hentai.org/uconfig.php", postData=confdict, addlHeaders=headers)

		self.permuteCookies()
		self.wg.saveCookies()

	# So exhen uses some irritating cross-site login hijinks.
	# Anyways, we need to copy the cookies for e-hentai to exhentai,
	# so we iterate over all cookies, and duplicate+modify the relevant
	# cookies.
	def permuteCookies(self):
		self.log.info("Fixing cookies")
		for cookie in self.wg.cj:
			if (
					"ipb_member_id" in cookie.name or
					"ipb_pass_hash" in cookie.name or
					"uconfig"       in cookie.name or
					'hath_perks'    in cookie.name
					):

				dup = copy.copy(cookie)
				dup.domain = 'exhentai.org'

				self.wg.addCookie(dup)


	# MOAR checking. We load the root page, and see if we have anything.
	# If we get an error, it means we're being sadpanda'ed (because it serves up a gif
	# rather then HTML, which causes getSoup() to error), and we should abort.
	def checkExAccess(self):
		try:
			self.wg.getSoup(self.urlBase)
			return True
		except ValueError:
			return False


	# -----------------------------------------------------------------------------------
	# The scraping parts
	# -----------------------------------------------------------------------------------



	def loadFeed(self, tag, pageOverride=None, includeExpunge=False):
		self.log.info("Retreiving feed content...",)
		if not pageOverride:
			pageOverride = 0  # Pages start at zero. Yeah....
		try:
			tag = urllib.parse.quote_plus(tag)
			pageUrl = self.urlFeed.format(search=tag, num=pageOverride)
			if includeExpunge:
				pageUrl = pageUrl + '&f_sh=on'
			soup = self.wg.getSoup(pageUrl)
		except urllib.error.URLError:
			self.log.critical("Could not get page from SadPanda!")
			self.log.critical(traceback.format_exc())
			return None

		return soup


	def getUploadTime(self, dateStr):
		# ParseDatetime COMPLETELY falls over on "YYYY-MM-DD HH:MM" formatted strings. Not sure why.
		# Anyways, dateutil.parser.parse seems to work ok, so use that.
		updateDate = dateutil.parser.parse(dateStr, yearfirst=True)
		ret = calendar.timegm(updateDate.timetuple())

		# Patch times for the local-GMT offset.
		# using `calendar.timegm(time.gmtime()) - time.time()` is NOT ideal, but it's accurate
		# to a second or two, and that's all I care about.
		gmTimeOffset = calendar.timegm(time.gmtime()) - time.time()
		ret = ret - gmTimeOffset
		return ret



	def parseItem(self, inRow):
		ret = {}
		itemType, pubDate, name, uploader = inRow.find_all("td")

		# Do not download any galleries we uploaded.
		if uploader.get_text().lower().strip() == settings.sadPanda['login'].lower():
			return None

		category = itemType.img['alt']
		if category.lower() in settings.sadPanda['sadPandaExcludeCategories']:
			self.log.info("Excluded category: '%s'. Skipping.", category)
			return False

		ret['seriesName'] = category.title()

		# If there is a torrent link, decompose it so the torrent link doesn't
		# show up in our parsing of the content link.
		if name.find("div", class_='it3'):
			name.find("div", class_='it3').decompose()

		ret['sourceUrl']  = name.a['href']
		ret['originName'] = name.a.get_text().strip()
		ret['retreivalTime'] = self.getUploadTime(pubDate.get_text())

		return ret

	def getFeed(self, searchTag, includeExpunge=False, pageOverride=None):
		# for item in items:
		# 	self.log.info(item)
		#

		ret = []

		soup = self.loadFeed(searchTag, pageOverride, includeExpunge)

		itemTable = soup.find("table", class_="itg")

		if not itemTable:
			return []

		rows = itemTable.find_all("tr", class_=re.compile("gtr[01]"))
		self.log.info("Found %s items on page.", len(rows))
		for row in rows:

			item = self.parseItem(row)
			if item:
				ret.append(item)


		return ret



	# TODO: Add the ability to re-acquire downloads that are
	# older then a certain age.
	def go(self):
		self.resetStuckItems()
		self.checkLogin()
		if not self.checkExAccess():
			raise ValueError("Cannot access ex! Wat?")

		for searchTag, includeExpunge in settings.sadPanda['sadPandaSearches']:

			dat = self.getFeed(searchTag, includeExpunge)

			self.processLinksIntoDB(dat)

			time.sleep(5)

# def getHistory():

# 	run = DbLoader()
# 	for x in range(18, 1150):
# 		dat = run.getFeed(pageOverride=x)
# 		run.processLinksIntoDB(dat)



def login():

	run = DbLoader()
	# run.checkLogin()
	# run.checkExAccess()
	for feed in settings.sadPanda['sadPandaSearches']:
		for x in range(8):
			ret = run.getFeed(feed, pageOverride=x)
			if not ret:
				break
			run.processLinksIntoDB(ret)

			time.sleep(5)
	# run.go()


if __name__ == "__main__":
	import utilities.testBase as tb

	with tb.testSetup(startObservers=False):
		# login()
		run = DbLoader()
		run.checkLogin()
		run.go()


