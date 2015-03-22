


import runStatus
runStatus.preloadDicts = False

# import Levenshtein as lv

import urllib.parse

import bs4
import copy
import readability.readability
import hashlib
import os.path
import TextScrape.RelinkLookup
import TextScrape.urlFuncs

import TextScrape.urlFuncs

import TextScrape.ProcessorBase


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




class GdocPageProcessor(TextScrape.ProcessorBase.PageProcessor):

	loggerPath = "Main.GdocPageProcessor"

	def __init__(self, pageUrl, loggerPath, tableKey, scannedDomains=None, tlds=None):
		self.loggerPath = loggerPath+".GDocExtract"
		self.pageUrl    = pageUrl
		self.tableKey = tableKey

		self._relinkDomains = set()
		for url in TextScrape.RelinkLookup.RELINKABLE:
			self._relinkDomains.add(url)


		self._tld            = set()
		self._scannedDomains = set()

		# Tell the path filtering mechanism that we can fetch google doc files
		# Not switchable, since not fetching google docs content from a google docs page
		# wouldn't work too well.
		self._scannedDomains.add('https://docs.google.com/document/')
		self._scannedDomains.add('https://docs.google.com/spreadsheets/')
		self._scannedDomains.add('https://drive.google.com/folderview')
		self._scannedDomains.add('https://drive.google.com/open')

		if not scannedDomains:
			scannedDomains = []
		if not tlds:
			tlds = []

		# Build the filtering structures for checking outgoing links.
		for tld in tlds:
			self._tld.add(tld)

		for domain in scannedDomains:
			self.installBaseUrl(domain)

		# File mapping LUT
		self.fMap = {}

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

		if 'sites.google.com/site/' in url:
			self._scannedDomains.add(url)

		elif 'google.' in netloc:
			self.log.info("Skipping URL: '%s'", url)

		else:

			base, tld = netloc.rsplit(".", 1)
			self._tld.add(tld)
			for tld in self._tld:
				self._scannedDomains.add("{main}.{tld}".format(main=base, tld=tld))
				# print(self._scannedDomains)



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

		# Expected format of tuples in ret:
		# fName, mimeType, content, fHash
		ret = []


		for fName, mimeType, content in resources:
			m = hashlib.md5()
			m.update(content)
			fHash = m.hexdigest()


			pseudoUrl = self.tableKey+fHash

			self.fMap[fName] = fHash

			fName = os.path.split(fName)[-1]

			self.log.info("Resource = '%s', '%s', '%s'", fName, mimeType, pseudoUrl)
			if mimeType in ["image/gif", "image/jpeg", "image/pjpeg", "image/png", "image/svg+xml", "image/vnd.djvu"]:
				self.log.info("Processing resource '%s' as an image file. (mimetype: %s)", fName, mimeType)
				ret.append((fName, mimeType, content, pseudoUrl))
			elif mimeType in ["application/octet-stream"]:
				self.log.info("Processing '%s' as an binary file.", fName)
				ret.append((fName, mimeType, content, pseudoUrl))
			else:
				self.log.warn("Unknown MIME Type? '%s', FileName: '%s'", mimeType, fName)

		if len(resources) == 0:
			self.log.info("File had no resource content!")

		return ret



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
		TextScrape.urlFuncs.canonizeUrls(soup, url)

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
				url = TextScrape.urlFuncs.urlClean(url)
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
				url = TextScrape.urlFuncs.urlClean(url)
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



	# Process a Google-Doc resource page.
	# This call does a set of operations to permute and clean a google doc page.
	def extractContent(self):
		ret['plainLinks'] = plainLinks
		ret['rsrcLinks']  = imageLinks
		ret['title']      = pgTitle
		ret['contents']   = pgBody




def test():
	print("Test mode!")
	import webFunctions
	import logSetup
	logSetup.initLogging()

	wg = webFunctions.WebGetRobust()
	# content = wg.getpage('http://www.arstechnica.com')
	scraper = GdocPageProcessor('https://docs.google.com/document/d/1ZdweQdjIBqNsJW6opMhkkRcSlrbgUN5WHCcYrMY7oqI', 'Main.Test', 'testinating')
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

