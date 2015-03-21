


import runStatus
runStatus.preloadDicts = False

# import Levenshtein as lv

import urllib.parse

import bs4
import copy
import readability.readability

import TextScrape.RelinkLookup

import LogBase



import TextScrape.gDocParse as gdp

class DownloadException(Exception):
	pass



########################################################################################################################
#
#	##     ##    ###    #### ##    ##     ######  ##          ###     ######   ######
#	###   ###   ## ##    ##  ###   ##    ##    ## ##         ## ##   ##    ## ##    ##
#	#### ####  ##   ##   ##  ####  ##    ##       ##        ##   ##  ##       ##
#	## ### ## ##     ##  ##  ## ## ##    ##       ##       ##     ##  ######   ######
#	##     ## #########  ##  ##  ####    ##       ##       #########       ##       ##
#	##     ## ##     ##  ##  ##   ###    ##    ## ##       ##     ## ##    ## ##    ##
#	##     ## ##     ## #### ##    ##     ######  ######## ##     ##  ######   ######
#
########################################################################################################################

def rebaseUrl(url, base):
	"""Rebase one url according to base"""

	parsed = urllib.parse.urlparse(url)
	if parsed.scheme == parsed.netloc == '':
		return urllib.parse.urljoin(base, url)
	else:
		return url


# All tags you need to look into to do link canonization
# source: http://stackoverflow.com/q/2725156/414272
# "These aren't necessarily simple URLs ..."
urlContainingTargets = [
	(False, 'a',          'href'),
	(False, 'applet',     'codebase'),
	(False, 'area',       'href'),
	(False, 'base',       'href'),
	(False, 'blockquote', 'cite'),
	(False, 'body',       'background'),
	(False, 'del',        'cite'),
	(False, 'form',       'action'),
	(False, 'frame',      'longdesc'),
	(False, 'frame',      'src'),
	(False, 'head',       'profile'),
	(False, 'iframe',     'longdesc'),
	(False, 'iframe',     'src'),
	(False, 'input',      'src'),
	(False, 'input',      'usemap'),
	(False, 'ins',        'cite'),
	(False, 'link',       'href'),
	(False, 'object',     'classid'),
	(False, 'object',     'codebase'),
	(False, 'object',     'data'),
	(False, 'object',     'usemap'),
	(False, 'q',          'cite'),
	(False, 'script',     'src'),
	(False, 'audio',      'src'),
	(False, 'button',     'formaction'),
	(False, 'command',    'icon'),
	(False, 'embed',      'src'),
	(False, 'html',       'manifest'),
	(False, 'input',      'formaction'),
	(False, 'source',     'src'),
	(False, 'video',      'poster'),
	(False, 'video',      'src'),
	(True,  'img',        'longdesc'),
	(True,  'img',        'src'),
	(True,  'img',        'usemap'),
]


GLOBAL_BAD = [
			'gprofiles.js',
			'netvibes.com',
			'accounts.google.com',
			'edit.yahoo.com',
			'add.my.yahoo.com',
			'public-api.wordpress.com',
			'r-login.wordpress.com',
			'twitter.com',
			'facebook.com',
			'public-api.wordpress.com',
			'wretch.cc',
			'ws-na.amazon-adsystem.com',
			'delicious.com',
			'paypal.com',
			'digg.com',
			'topwebfiction.com',
			'/page/page/',
			'addtoany.com',
			'stumbleupon.com',
			'delicious.com',
			'reddit.com',
			'newsgator.com',
			'technorati.com',
	]

GLOBAL_DECOMPOSE_BEFORE = [
			{'name'     : 'likes-master'},  # Bullshit sharing widgets
			{'id'       : 'jp-post-flair'},
			{'class'    : 'post-share-buttons'},
			{'class'    : 'commentlist'},  # Scrub out the comments so we don't try to fetch links from them
			{'class'    : 'comments'},
			{'id'       : 'comments'},
		]

GLOBAL_DECOMPOSE_AFTER = []

class HtmlPageProcessor(LogBase.LoggerMixin):


	loggerPath = "Main.HtmlProc"

	IGNORE_MALFORMED_URLS = False
	FOLLOW_GOOGLE_LINKS = True

	# # `decompose` and `decomposeBefore` are defined in the child plugins
	# decompose       = []
	# decomposeBefore = []


	# fileDomains     = []

	# allImages       = False
	# tld             = set()

	# stripTitle = ''

	def __init__(self, baseUrls, pageUrl, pgContent, loggerPath, **kwargs):
		self.loggerPath = loggerPath

		self._tld           = set()
		self._fileDomains   = set()
		self.scannedDomains = set()

		self.content = pgContent
		self.baseUrls = baseUrls
		self.pageUrl = pageUrl

		kwargs.setdefault("badwords",         [])
		kwargs.setdefault("decompose",        [])
		kwargs.setdefault("decomposeBefore",  [])
		kwargs.setdefault("fileDomains",      [])
		kwargs.setdefault("allImages",        True)
		kwargs.setdefault("tld",              set())
		kwargs.setdefault("stripTitle",       '')


		self.badwords        = kwargs["badwords"]
		self.decompose       = kwargs["decompose"]
		self.decomposeBefore = kwargs["decomposeBefore"]
		self.fileDomains     = kwargs["fileDomains"]
		self.allImages       = kwargs["allImages"]
		self.tld             = kwargs["tld"]
		self.stripTitle      = kwargs["stripTitle"]




		self._badwords       = set(GLOBAL_BAD)

		# `_decompose` and `_decomposeBefore` are the actual arrays of items to decompose, that are loaded with the contents of
		# `decompose` and `decomposeBefore` on plugin initialization
		self._decompose       = copy.copy(GLOBAL_DECOMPOSE_AFTER)
		self._decomposeBefore = copy.copy(GLOBAL_DECOMPOSE_BEFORE)

		self._relinkDomains = set()
		for url in TextScrape.RelinkLookup.RELINKABLE:
			self._relinkDomains.add(url)

		if isinstance(self.baseUrls, (set, list)):
			for url in self.baseUrls:
				self.scannedDomains.add(url)
				self._fileDomains.add(urllib.parse.urlsplit(url.lower()).netloc)
		else:
			self.scannedDomains.add(self.baseUrls)
			self._fileDomains.add(urllib.parse.urlsplit(self.baseUrls.lower()).netloc)

		self._scannedDomains = set()

		if self.FOLLOW_GOOGLE_LINKS:
			# Tell the path filtering mechanism that we can fetch google doc files
			self._scannedDomains.add('https://docs.google.com/document/')
			self._scannedDomains.add('https://docs.google.com/spreadsheets/')
			self._scannedDomains.add('https://drive.google.com/folderview')
			self._scannedDomains.add('https://drive.google.com/open')


		# Move the plugin-defined decompose calls into the control lists
		for item in self.decompose:
			self._decompose.append(item)

		for item in self.decomposeBefore:
			self._decomposeBefore.append(item)

		for item in self.badwords:
			self._badwords.add(item)

		for item in self.fileDomains:
			self._fileDomains.add(item)

		# You need to install the TLDs before the baseUrls, because the baseUrls
		# are permuted driven by the TLDs, to some extent.
		for item in self.tld:
			self._tld.add(item)

		# Lower case all the domains, since they're not case sensitive, and it case mismatches can break matching.
		# We also extract /just/ the netloc, so http/https differences don't cause a problem.
		for url in self.scannedDomains:
			self.installBaseUrl(url)


		tmp = list(self._scannedDomains)
		tmp.sort()
		# for url in tmp:
		# 	self.log.info("Scanned domain:		%s", url)


	def installBaseUrl(self, url):
		netloc = urllib.parse.urlsplit(url.lower()).netloc
		if not netloc:
			raise ValueError("One of the scanned domains collapsed down to an empty string: '%s'!" % url)

		# Generate the possible wordpress netloc values.
		if 'wordpress.com' in netloc:
			subdomain, mainDomain, tld = netloc.rsplit(".")[-3:]

			self._scannedDomains.add("www.{sub}.{main}.{tld}".format(sub=subdomain, main=mainDomain, tld=tld))
			self._scannedDomains.add("{sub}.{main}.{tld}".format(sub=subdomain, main=mainDomain, tld=tld))
			self._scannedDomains.add("www.{sub}.files.{main}.{tld}".format(sub=subdomain, main=mainDomain, tld=tld))
			self._scannedDomains.add("{sub}.files.{main}.{tld}".format(sub=subdomain, main=mainDomain, tld=tld))

		# Blogspot is annoying and sometimes a single site is spread over several tlds. *.com, *.sg, etc...
		if 'blogspot.' in netloc:
			subdomain, mainDomain, tld = netloc.rsplit(".")[-3:]
			self._tld.add(tld)
			for tld in self._tld:
				self._scannedDomains.add("www.{sub}.{main}.{tld}".format(sub=subdomain, main=mainDomain, tld=tld))
				self._scannedDomains.add("{sub}.{main}.{tld}".format(sub=subdomain, main=mainDomain, tld=tld))

				self._fileDomains.add('bp.blogspot.{tld}'.format(tld=tld))


		if 'sites.google.com/site/' in url:
			self._scannedDomains.add(url)

		elif 'google.' in netloc:
			self.log.info("Skipping URL: '%s'", url)

		else:

			base, tld = netloc.rsplit(".", 1)
			self._tld.add(tld)
			for tld in self._tld:
				self._scannedDomains.add("{main}.{tld}".format(main=base, tld=tld))
				print(self._scannedDomains)



	########################################################################################################################
	#
	#	 ######    #######   #######   ######   ##       ########    ########   #######   ######   ######
	#	##    ##  ##     ## ##     ## ##    ##  ##       ##          ##     ## ##     ## ##    ## ##    ##
	#	##        ##     ## ##     ## ##        ##       ##          ##     ## ##     ## ##       ##
	#	##   #### ##     ## ##     ## ##   #### ##       ######      ##     ## ##     ## ##        ######
	#	##    ##  ##     ## ##     ## ##    ##  ##       ##          ##     ## ##     ## ##             ##
	#	##    ##  ##     ## ##     ## ##    ##  ##       ##          ##     ## ##     ## ##    ## ##    ##
	#	 ######    #######   #######   ######   ######## ########    ########   #######   ######   ######
	#
	########################################################################################################################


	def processGdocResources(self, resources):

		self.fMap = {}


		for fName, mimeType, content in resources:
			m = hashlib.md5()
			m.update(content)
			fHash = m.hexdigest()

			hashName = self.tableKey+fHash

			self.fMap[fName] = fHash

			fName = os.path.split(fName)[-1]

			self.log.info("Resource = '%s', '%s', '%s'", fName, mimeType, hashName)
			if mimeType in ["image/gif", "image/jpeg", "image/pjpeg", "image/png", "image/svg+xml", "image/vnd.djvu"]:
				self.log.info("Processing resource '%s' as an image file. (mimetype: %s)", fName, mimeType)
				self.upsert(hashName, istext=False)
				self.saveFile(hashName, mimeType, fName, content)
			elif mimeType in ["application/octet-stream"]:
				self.log.info("Processing '%s' as an binary file.", fName)
				self.upsert(hashName, istext=False)
				self.saveFile(hashName, mimeType, fName, content)
			else:
				self.log.warn("Unknown MIME Type? '%s', FileName: '%s'", mimeType, fName)

		if len(resources) == 0:
			self.log.info("File had no resource content!")



	def cleanGdocPage(self, soup, url):


		doc = readability.readability.Document(str(soup))

		title = self.extractTitle(soup, doc, url)

		for span in soup.find_all("span"):
			span['style'] = ''

		return title, soup



	# Hook so plugins can modify the internal URLs as part of the relinking process
	def preprocessGdocReaderUrl(self, inUrl):
		if inUrl.lower().endswith("/preview"):
			inUrl = inUrl[:-len("/preview")]

		return inUrl


	def convertToGdocReaderImage(self, srcUrl):

		itemHash = None
		for rscEnd in self.fMap:
			if srcUrl.endswith(rscEnd):
				itemHash = self.fMap[rscEnd]

		# if srcUrl in self.fMap:
		# 	url = self.fMap[srcUrl]
		# elif any([fUrl in url for fUrl in self.fMap]):
		# 	print('wat')
		# 	raise ValueError("Unknown image URL! = '%s'" % url)
		if not itemHash:
			raise ValueError("Unknown image URL! = '%s' (hash '%s')" % (srcUrl, itemHash))

		url = '/books/render?mdsum=%s' % urllib.parse.quote(itemHash)

		return url



	def processGdocPage(self, url, content):
		dummy_fName, content = content
		print("Page size: ", len(content))
		soup = bs4.BeautifulSoup(content)
		self.canonizeUrls(soup, url)

		pgTitle, soup = self.cleanGdocPage(soup, url)

		self.extractLinks(soup, url)
		self.log.info("Page title = '%s'", pgTitle)
		soup = self.relink(soup, imRelink=self.convertToGdocReaderImage)

		url = self.preprocessGdocReaderUrl(url)
		url = gdp.trimGDocUrl(url)
		# Since the content we're extracting will be embedded into another page, we want to
		# strip out the <body> and <html> tags. `unwrap()`  replaces the soup with the contents of the
		# tag it's called on. We end up with just the contents of the <body> tag.
		soup.body.unwrap()
		pgBody = soup.prettify()

		self.updateDbEntry(url=url, title=pgTitle, contents=pgBody, mimetype='text/html', dlstate=2)




	def retreiveGoogleDoc(self, url):


		self.log.info("Should fetch google doc at '%s'", url)
		doc = gdp.GDocExtractor(url)



		attempts = 0

		mainPage = None
		while 1:
			attempts += 1
			try:
				mainPage, resources = doc.extract()
			except TypeError:
				self.log.critical('Extracting item failed!')
				for line in traceback.format_exc().strip().split("\n"):
					self.log.critical(line.strip())


				url = gdp.trimGDocUrl(url)
				if not url.endswith("/pub"):
					url = url+"/pub"
				self.log.info("Attempting to access as plain content instead.")
				url = self.urlClean(url)
				self.putNewUrl(url)
				return
			if mainPage:
				break
			if attempts > 3:
				raise DownloadException

		self.processGdocResources(resources)

		self.processGdocPage(url, mainPage)

	def retreiveGoogleFile(self, url):


		self.log.info("Should fetch google file at '%s'", url)
		doc = gdp.GFileExtractor(url)

		attempts = 0

		while 1:
			attempts += 1
			try:
				content, fName, mType = doc.extract()
			except TypeError:
				self.log.critical('Extracting item failed!')
				for line in traceback.format_exc().strip().split("\n"):
					self.log.critical(line.strip())

				if not url.endswith("/pub"):
					url = url+"/pub"

				self.log.info("Attempting to access as plain content instead.")
				url = self.urlClean(url)
				url = gdp.trimGDocUrl(url)
				self.putNewUrl(url)
				return
			if content:
				break
			if attempts > 3:
				raise DownloadException


			self.log.error("No content? Retrying!")

		self.dispatchContent(url, content, fName, mType)


	def extractGoogleDriveFolder(self, driveUrl):
		'''
		Extract all the relevant links from a google drive directory, and push them into
		the queued URL queue.

		'''

		docReferences, pgTitle = gdp.GDocExtractor.getDriveFileUrls(driveUrl)
		# print('docReferences', docReferences)
		for dummy_title, url in docReferences:
			url = gdp.trimGDocUrl(url)
			self.putNewUrl(url)

		self.log.info("Generating google drive disambiguation page!")
		soup = gdp.makeDriveDisambiguation(docReferences, pgTitle)
		# print(disamb)

		soup = self.relink(soup)

		disamb = soup.prettify()

		self.updateDbEntry(url=driveUrl, title=pgTitle, contents=disamb, mimetype='text/html', dlstate=2)


		self.log.info("Found %s items in google drive directory", len(docReferences))



	def putNewUrl(self, url, baseUrl=None, istext=True):
		if not url.lower().startswith("http"):
			if baseUrl:
				# If we have a base-url to extract the scheme from, we pull that out, concatenate
				# it onto the rest of the url segments, and then unsplit that back into a full URL
				scheme = urllib.parse.urlsplit(baseUrl.lower()).scheme
				rest = urllib.parse.urlsplit(baseUrl.lower())[1:]
				params = (scheme, ) + rest

				# self.log.info("Had to add scheme (%s) to URL: '%s'", scheme, url)
				url = urllib.parse.urlunsplit(params)

			elif self.IGNORE_MALFORMED_URLS:
				self.log.error("Skipping a malformed URL!")
				self.log.error("Bad URL: '%s'", url)
				return
			else:
				raise ValueError("Url isn't a url: '%s'" % url)
		if gdp.isGdocUrl(url) or gdp.isGFileUrl(url):
			if gdp.trimGDocUrl(url) != url:
				raise ValueError("Invalid link crept through! Link: '%s'" % url)


		if not url.lower().startswith('http'):
			raise ValueError("Failure adding scheme to URL: '%s'" % url)

		if not self.checkDomain(url) and istext:
			raise ValueError("Invalid url somehow got through: '%s'" % url)

		if '/view/export?format=zip' in url:
			raise ValueError("Wat?")
		self.newLinkQueue.put((url, istext))



def test():
	print("Test mode!")
	import webFunctions
	import logSetup
	logSetup.initLogging()

	wg = webFunctions.WebGetRobust()
	content = wg.getpage('http://www.arstechnica.com')
	scraper = HtmlPageProcessor(['http://www.arstechnica.com', "http://cdn.arstechnica.com/"], 'http://www.arstechnica.com', content, 'Main.Test', tld=['com', 'net'])
	print(scraper)
	extr = scraper.extractContent()
	for link in extr['fLinks']:
		print(link)
	print()
	print()
	print()
	for link in extr['iLinks']:
		print(link)
	# print(extr['fLinks'])


if __name__ == "__main__":
	test()

