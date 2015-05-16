
import logSetup
if __name__ == "__main__":
	print("Initializing logging")
	logSetup.initLogging()

import TextScrape.MonitorBase
import dateutil.parser
import urllib.parse
import webFunctions
import json
import time
import calendar
import urllib.error
import settings
import TextScrape.NovelMixin
import roman


from concurrent.futures import ThreadPoolExecutor
import bs4
import bs4.element

def isnumeric(value):
	return str(value).replace(".", "").replace("-", "").isdigit()

def parseDigit(inStr, curValue):
	'''
	Try to parse a value as either a integer, or if that
	fails, a roman numeral value.
	Returns the new value if it parsed successfully, the original if
	not.
	'''

	# 下 and 上 mean last and first volume in a set respectively.
	# Anyways, clear that out so the parsing actually works.
	inStr = inStr.replace("上", "")
	inStr = inStr.replace("下", "")

	# And the second of a set
	inStr = inStr.replace("中", "")

	# And just "a volume"
	inStr = inStr.replace("巻", "")

	# "Gaiden", or side-story
	# Inject a giant offset
	inStr = inStr.replace("外伝 ", "1000")
	inStr = inStr.replace("外伝", "1000")


	value = inStr.split()[-1]
	if isnumeric(value):
		curValue = float(value)
	else:
		try:
			# print("Parsing as roman numeral", value)
			curValue = roman.fromRoman(value.upper())
		except roman.InvalidRomanNumeralError:
			print("Roman numeral error?", value.upper())
			import traceback
			traceback.print_exc()
			pass
	return curValue


class Monitor(TextScrape.NovelMixin.NovelMixin, TextScrape.MonitorBase.MonitorBase):
	tableName = 'books_lndb'
	loggerPath = 'Main.Text.LNDB.Monitor'
	pluginName = 'LNDBMonitor'
	plugin_type = 'SeriesMonitor'

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	baseurl = 'http://lndb.info/'

	'''
	No login is needed for the LNDB scraper, because they don't have lists or anything.
	'''

	THREADS = 8

	def extractCookie(self):
		csrf_test_name = None
		for cookie in self.wg.cj:

			if 'lndb.info' in cookie.domain and \
				cookie.name == 'csrf_cookie_name':
				csrf_test_name = cookie.value

		return csrf_test_name


	def getCsrfCookie(self):
		'''
			If we already have a CSRF protection cookie, just use it.
			otherwise, do a simple fetch to get one.
		'''
		cookie = self.extractCookie()
		if not cookie:
			pg = self.wg.getSoup('http://lndb.info/general/recent_changes/')
		cookie = self.extractCookie()

		if not cookie:
			self.log.error("Cannot find CSRF cookie!")
			raise ValueError("No CSRF Cookie!")

		return cookie


	def checkLogin(self):

		checkPage = self.wg.getpage(self.baseurl)
		if not "you are logged in." in checkPage:
			self.log.info("Whoops, need to get Login cookie")
		else:
			self.log.info("Still logged in")
			return



		CsrfToken = self.getCsrfCookie()

		addlHeaders = {'Referer': 'http://lndb.info/auth/login'}
		logondict   = {
						'csrf_test_name' : CsrfToken,
						"login"          : settings.lndb["login"],
						"password"       : settings.lndb["passwd"],
						"remember"       : "1",
						"submit_login"   : "Log in"
					}


		getPage = self.wg.getpage(r"http://lndb.info/auth/login", postData=logondict, addlHeaders=addlHeaders)
		if "Incorrect login" in getPage:
			self.log.error("Login failed!")
			raise ValueError("Cannot login to LNDB. Is your login/password valid?")
		elif "you are logged in." in getPage:
			self.log.info("Logged in successfully!")

		self.wg.saveCookies()


	##############################################################################################################################
	#
	#	 ######  ##     ##    ###    ##    ##  ######   ########    ##     ##  #######  ##    ## #### ########  #######  ########
	#	##    ## ##     ##   ## ##   ###   ## ##    ##  ##          ###   ### ##     ## ###   ##  ##     ##    ##     ## ##     ##
	#	##       ##     ##  ##   ##  ####  ## ##        ##          #### #### ##     ## ####  ##  ##     ##    ##     ## ##     ##
	#	##       ######### ##     ## ## ## ## ##   #### ######      ## ### ## ##     ## ## ## ##  ##     ##    ##     ## ########
	#	##       ##     ## ######### ##  #### ##    ##  ##          ##     ## ##     ## ##  ####  ##     ##    ##     ## ##   ##
	#	##    ## ##     ## ##     ## ##   ### ##    ##  ##          ##     ## ##     ## ##   ###  ##     ##    ##     ## ##    ##
	#	 ######  ##     ## ##     ## ##    ##  ######   ########    ##     ##  #######  ##    ## ####    ##     #######  ##     ##
	#
	##############################################################################################################################

	def getChanges(self, page_offset):

		CsrfToken = self.getCsrfCookie()

		pg = self.wg.getpage('http://lndb.info/general/recent_changes/',
				postData={
							'page_offset'    : page_offset,
							'page_limit'     : 100,
							'csrf_test_name' : CsrfToken,
						}
					)

		data = json.loads(pg)

		assert 'revisions' in data

		items = {}
		for item in data['revisions']:
			if item['light_novel_title']:

				date     = dateutil.parser.parse(item['revision_date'])
				date     = calendar.timegm(date.timetuple())

				title    = item['light_novel_title'].strip()

				line     = {'title' : title, 'date' : date}

				# Skip items if it's an older update
				if title in items:
					if items[title]['date'] > date:
						continue
				items[title] = line
		return items

	def upsertChanges(self, page_offset=1):
		changes = 0
		items = self.getChanges(page_offset)
		for item in items.values():
			self.upsertNovelName(item['title'])

			have = self.getRowByValue(cTitle=item['title'])
			if have and have['lastChanged'] >= item['date']:
				continue
			elif have:
				self.log.info("Item changed: '%s', '%s'", have['lastChanged'], have['lastChanged'] - item['date'])
				self.updateDbEntry(have['dbId'], changeState=0, lastChanged=have['lastChanged'])
			else:
				self.insertIntoDb(cTitle=item['title'], lastChanged=item['date'], firstSeen=time.time(), seriesEntry=True)
			changes += 1

		numItemsOnPage = len(items)
		self.log.info("Changed items to re-scan: %s. Total distinct items on page: %s'", changes, numItemsOnPage)

		return numItemsOnPage

	###########################################################################################################################################
	#
	#	 ######   #######  ##    ## ######## ######## ##    ## ########    ##     ## ########  ########     ###    ######## ######## ########
	#	##    ## ##     ## ###   ##    ##    ##       ###   ##    ##       ##     ## ##     ## ##     ##   ## ##      ##    ##       ##     ##
	#	##       ##     ## ####  ##    ##    ##       ####  ##    ##       ##     ## ##     ## ##     ##  ##   ##     ##    ##       ##     ##
	#	##       ##     ## ## ## ##    ##    ######   ## ## ##    ##       ##     ## ########  ##     ## ##     ##    ##    ######   ########
	#	##       ##     ## ##  ####    ##    ##       ##  ####    ##       ##     ## ##        ##     ## #########    ##    ##       ##   ##
	#	##    ## ##     ## ##   ###    ##    ##       ##   ###    ##       ##     ## ##        ##     ## ##     ##    ##    ##       ##    ##
	#	 ######   #######  ##    ##    ##    ######## ##    ##    ##        #######  ##        ########  ##     ##    ##    ######## ##     ##
	#
	###########################################################################################################################################



	'''
	Source items:
	seriesEntry - Is this the entry for a series, or a individual volume/chapter
	cTitle      - Chapter Title (cleaned for URL use)
	oTitle      - Chapter Title (Raw, can contain non-URL safe chars)
	jTitle      - Title in Japanese
	vTitle      - Volume Title
	jvTitle     - Japanese Volume Title
	series      - Light Novel
	pub	        - Publisher
	label       - Light Novel Label
	volNo       - Volumes
	author      - Author
	illust      - Illustrator
	target      - Target Readership
	relDate     - Release Date
	covers      - Cover Array
	'''

	def getSoupForSeriesItem(self, itemtitle):
		url      = urllib.parse.urljoin(self.baseurl, '/light_novel/view/' + itemtitle.replace(' ', '_'))
		referrer = urllib.parse.urljoin(self.baseurl, '/light_novel/' + itemtitle.replace(' ', '_'))

		soup = None
		for x in range(3):
			try:
				# You have to specify the 'X-Requested-With' param, or you'll get a 404
				soup = self.wg.getSoup(url, addlHeaders={'Referer': referrer, 'X-Requested-With': 'XMLHttpRequest'})
				break
			except urllib.error.URLError:
				time.sleep(4)
				# Randomize the user agent again
				self.wg = webFunctions.WebGetRobust(logPath=self.loggerPath+".Web")
		if not soup:
			raise ValueError("Could not retreive page!")
		return soup

	def extractSeriesInfo(self, soup):
		content = soup.find('div', class_='lightnovelcontent')

		dataLut = {
			'Japanese Title'        : 'jTitle',
			'Volume Title'          : 'oTitle',
			'Japanese Volume Title' : 'jvTitle',
			'Light Novel'           : 'series',
			'Publisher'             : 'pub',
			'Light Novel Label'     : 'label',
			'Author'                : 'author',
			'Illustrator'           : 'illust',
			'Target Readership'     : 'target',
			'Volumes'               : 'volNo',
			'Release Date'          : 'relDate',
			'Pages'                 : None,
			'ISBN-10'               : None,
			'ISBN-13'               : None,
			'Height (cm)'           : None,
			'Width (cm)'            : None,
			'Thickness (cm)'        : None,
			'Online Shops'          : None,
		}

		assert content != None
		itemTitle = content.find('div', class_='secondarytitle').get_text().strip()

		infoDiv = content.find('div', class_="secondary-info")

		rows = infoDiv.find_all('tr')

		self.log.info("Found %s data rows for item!", len(rows))

		kwargs = {}

		for tr in rows:
			tds = tr.find_all('td')
			if len(tds) != 2:
				self.log.error("Row with wrong number of items?")
				continue
			desc, cont = tds
			desc = desc.get_text().strip()
			cont = cont.get_text().strip()

			if desc in dataLut:
				kwargs[dataLut[desc]] = cont

		return kwargs

	def extractCovers(self, soup, dbId):
		coverDiv = soup.find('div', class_='view-covers')
		if not coverDiv:
			self.log.info("No covers!")
			return

		for child in coverDiv.find_all('div', recursive=False):
			# print("------------------------")
			self.processCoverDiv(child, dbId)
			# print("------------------------")

	def processCoverDiv(self, divContent, dbId):

		image = divContent.find('a', class_='highslide')
		desc = divContent.find('div', class_='highslide-caption')

		imgUrl = urllib.parse.urljoin(self.baseurl, image['href'])

		title = desc.find('div', class_='cover-title')
		if title.span:
			title.span.decompose()
		title = title.get_text().strip()

		volume = None
		chapter = None
		# Iterate over only the child items that are strings.
		itemStrings = [item for item in desc.children if isinstance(item, bs4.element.NavigableString)]
		for child in itemStrings:

			if child.startswith("Volume:"):
				volume = parseDigit(child, volume)

			# I haven't seen chapter covers in LNDB, but what the hell.
			if child.startswith("Chapter:"):
				chapter = parseDigit(child, volume)


		if self.checkHaveCover(dbId, volume, chapter):
			return

		imgCont = self.wg.getpage(imgUrl)
		fName = urllib.parse.urlsplit(imgUrl).path.split("/")[-1]

		# print(fName)
		# print("Chapter", chapter, "Volume", volume)

		self.upsertCover(fName, imgCont, dbId, volume, chapter, title)




	def updateSeriesItem(self, item):
		# print(item)
		soup = self.getSoupForSeriesItem(item['cTitle'])
		data = self.extractSeriesInfo(soup)

		self.extractCovers(soup, item['dbId'])

		self.updateDbEntry(item['dbId'], changeState=2, **data)



	###########################################################################################################################################
	#
	#	########    ###     ######  ##    ##    ##     ##    ###    ##    ##    ###     ######   ######## ##     ## ######## ##    ## ########
	#	   ##      ## ##   ##    ## ##   ##     ###   ###   ## ##   ###   ##   ## ##   ##    ##  ##       ###   ### ##       ###   ##    ##
	#	   ##     ##   ##  ##       ##  ##      #### ####  ##   ##  ####  ##  ##   ##  ##        ##       #### #### ##       ####  ##    ##
	#	   ##    ##     ##  ######  #####       ## ### ## ##     ## ## ## ## ##     ## ##   #### ######   ## ### ## ######   ## ## ##    ##
	#	   ##    #########       ## ##  ##      ##     ## ######### ##  #### ######### ##    ##  ##       ##     ## ##       ##  ####    ##
	#	   ##    ##     ## ##    ## ##   ##     ##     ## ##     ## ##   ### ##     ## ##    ##  ##       ##     ## ##       ##   ###    ##
	#	   ##    ##     ##  ######  ##    ##    ##     ## ##     ## ##    ## ##     ##  ######   ######## ##     ## ######## ##    ##    ##
	#
	###########################################################################################################################################


	def fetchThread(self, todo):
		for item in todo:
			if item['seriesEntry']:
				# print(item)
				self.updateSeriesItem(item)
			else:
				raise ValueError("How did a non-series-entry item get created?")
			time.sleep(1)

	def updateOutdated(self):
		todo = self.getRowsByValue(changeState=0)

		if todo:

			def iter_baskets_from(items, maxbaskets=self.THREADS):
				'''generates evenly balanced baskets from indexable iterable'''
				item_count = len(items)
				baskets = min(item_count, maxbaskets)
				for x_i in range(baskets):
					yield [items[y_i] for y_i in range(x_i, item_count, baskets)]

			linkLists = iter_baskets_from(todo, maxbaskets=self.THREADS)

			with ThreadPoolExecutor(max_workers=self.THREADS) as executor:

				for linkList in linkLists:
					executor.submit(self.fetchThread, linkList)

				executor.shutdown(wait=True)





	def go(self):
		# # Login if needed:
		self.checkLogin()

		# # Check for new changes
		self.upsertChanges()

		# And then fetch and update as needed.
		self.updateOutdated()

	def scanAllSeries(self):
		offset = 0
		while True:
			x = self.upsertChanges(page_offset=offset)
			if x == 0:
				break
			time.sleep(2.5)

			offset += 1

	def testRun(self):


		tests = [
			'Shizuru-san_series',
			# 'Ane_Ane_Suiei_Club',
			# 'Shokugeki_no_Souma_~a_la_carte~',
			# 'Steamheavens_Freaks',
			# 'Tenjou_Ugatsu_Shinma_no_Ken',
			# 'saiyaku sensen no overlord',
			# 'Boku_to_Majoshiki_Apocalypse',
			# 'Hagane_no_Shirousagi_Kishidan',
			# 'Vamp!',
			# 'Shiritsu!_Sanjyuusan_Gendou_Gakuin',
			# 'Magical_Warfare',
		]
		for test in tests:
			soup = self.getSoupForSeriesItem(test)
			data = self.extractSeriesInfo(soup)
			self.extractCovers(soup, -1)

			print(data)

def test():
	scrp = Monitor()
	# scrp.scanAllSeries()
	# scrp.updateOutdated()
	# scrp.testRun()
	scrp.go()
	# scrp.retreiveItemFromUrl(scrp.startUrl)


if __name__ == "__main__":
	test()




