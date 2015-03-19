


import runStatus
runStatus.preloadDicts = False

# import Levenshtein as lv

import logging
import settings
import urllib.parse
import threading

import os
import bs4
import os.path
import readability.readability

import TextScrape.RelinkLookup

import nameTools



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


class HtmlPageProcessor():


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
		self.loggers = {}
		self.lastLoggerIndex = 1

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




		self._badwords       = set([
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
			])

		# `_decompose` and `_decomposeBefore` are the actual arrays of items to decompose, that are loaded with the contents of
		# `decompose` and `decomposeBefore` on plugin initialization
		self._decompose       = []
		self._decomposeBefore = [
			{'name'     : 'likes-master'},  # Bullshit sharing widgets
			{'id'       : 'jp-post-flair'},
			{'class'    : 'commentlist'},  # Scrub out the comments so we don't try to fetch links from them
			{'class'    : 'post-share-buttons'},
			{'class'    : 'comments'},
			{'id'       : 'comments'},
		]

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

	# More hackiness to make sessions intrinsically thread-safe.
	def __getattribute__(self, name):

		threadName = threading.current_thread().name
		if name == "log":
			if "Thread-" in threadName:
				if threadName not in self.loggers:
					self.loggers[threadName] = logging.getLogger("%s.Thread-%d" % (self.loggerPath, self.lastLoggerIndex))
					self.lastLoggerIndex += 1

			# If we're not called in the context of a thread, just return the base log-path
			else:
				self.loggers[threadName] = logging.getLogger("%s" % (self.loggerPath,))
			return self.loggers[threadName]

		else:
			return object.__getattribute__(self, name)

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
	#	 ######   ######  ########     ###    ########  #### ##    ##  ######      ######## ##     ## ##    ##  ######  ######## ####  #######  ##    ##  ######
	#	##    ## ##    ## ##     ##   ## ##   ##     ##  ##  ###   ## ##    ##     ##       ##     ## ###   ## ##    ##    ##     ##  ##     ## ###   ## ##    ##
	#	##       ##       ##     ##  ##   ##  ##     ##  ##  ####  ## ##           ##       ##     ## ####  ## ##          ##     ##  ##     ## ####  ## ##
	#	 ######  ##       ########  ##     ## ########   ##  ## ## ## ##   ####    ######   ##     ## ## ## ## ##          ##     ##  ##     ## ## ## ##  ######
	#	      ## ##       ##   ##   ######### ##         ##  ##  #### ##    ##     ##       ##     ## ##  #### ##          ##     ##  ##     ## ##  ####       ##
	#	##    ## ##    ## ##    ##  ##     ## ##         ##  ##   ### ##    ##     ##       ##     ## ##   ### ##    ##    ##     ##  ##     ## ##   ### ##    ##
	#	 ######   ######  ##     ## ##     ## ##        #### ##    ##  ######      ##        #######  ##    ##  ######     ##    ####  #######  ##    ##  ######
	#
	########################################################################################################################



	def urlClean(self, url):
		# Google docs can be accessed with or without the '/preview' postfix
		# We want to remove this if it's present, so we don't duplicate content.
		url = gdp.trimGDocUrl(url)

		while True:
			url2 = urllib.parse.unquote(url)
			url2 = url2.split("#")[0]
			if url2 == url:
				break
			url = url2

		# Clean off whitespace.
		url = url.strip()

		return url

	def getItem(self, itemUrl):

		content, handle = self.wg.getpage(itemUrl, returnMultiple=True)
		if not content or not handle:
			raise ValueError("Failed to retreive file from page '%s'!" % itemUrl)

		fileN = urllib.parse.unquote(urllib.parse.urlparse(handle.geturl())[2].split("/")[-1])
		fileN = bs4.UnicodeDammit(fileN).unicode_markup
		mType = handle.info()['Content-Type']

		# If there is an encoding in the content-type (or any other info), strip it out.
		# We don't care about the encoding, since WebFunctions will already have handled that,
		# and returned a decoded unicode object.

		if mType and ";" in mType:
			mType = mType.split(";")[0].strip()


		self.log.info("Retreived file of type '%s', name of '%s' with a size of %0.3f K", mType, fileN, len(content)/1000.0)
		return content, fileN, mType

	# Hook so plugins can modify the internal URLs as part of the relinking process
	def preprocessReaderUrl(self, inUrl):
		return inUrl


	def convertToReaderUrl(self, inUrl):
		inUrl = self.urlClean(inUrl)
		inUrl = self.preprocessReaderUrl(inUrl)
		# The link will have been canonized at this point
		url = '/books/render?url=%s' % urllib.parse.quote(inUrl)
		return url

	# check if domain `url` is a sub-domain of the scanned domains.
	def checkDomain(self, url):
		# if "drive" in url:
		for rootUrl in self._scannedDomains:
			if urllib.parse.urlsplit(url).netloc:
				if urllib.parse.urlsplit(url).netloc == rootUrl:
					return True

			if url.lower().startswith(rootUrl):
				return True

		# print("CheckDomain False", url)
		return False

	def checkFollowGoogleUrl(self, url):
		'''
		I don't want to scrape outside of the google doc document context.

		Therefore, if we have a URL that's on docs.google.com, and doesn't have
		'/document/d/ in the URL, block it.
		'''
		# Short circuit for non docs domains
		url = url.lower()
		netloc = urllib.parse.urlsplit(url).netloc
		if not "docs.google.com" in netloc:
			return True

		if '/document/d/' in url:
			return True

		return False


	# check if domain `url` is a sub-domain of the domains we should relink.
	def checkRelinkDomain(self, url):
		# if "drive" in url:
		# 	print("CheckDomain", any([rootUrl in url.lower() for rootUrl in self._scannedDomains]), url)
		return any([rootUrl in url.lower() for rootUrl in self._relinkDomains])


	def processLinkItem(self, url, baseUrl):
		url = gdp.clearOutboundProxy(url)
		url = gdp.clearBitLy(url)

		# Filter by domain
		if not self.checkDomain(url):
			# print("Filtering", self.checkDomain(url), url)
			return


		# and by blocked words
		for badword in self._badwords:
			if badword in url:
				# print("hadbad", self.checkDomain(url), url)

				return



		if not self.checkFollowGoogleUrl(url):
			return

		url = self.urlClean(url)

		if "google.com" in urllib.parse.urlsplit(url.lower()).netloc:
			url = gdp.trimGDocUrl(url)

			if url.startswith('https://docs.google.com/document/d/images'):
				return

			# self.log.info("Resolved URL = '%s'", url)
			return self.processNewUrl(url, baseUrl)
			# self.log.info("New G link: '%s'", url)

		else:
			# Remove any URL fragments causing multiple retreival of the same resource.
			if url != gdp.trimGDocUrl(url):
				print('Old URL: "%s"' % url)
				print('Trimmed: "%s"' % gdp.trimGDocUrl(url))
				raise ValueError("Wat? Url change? Url: '%s'" % url)
			return self.processNewUrl(url, baseUrl)
			# self.log.info("Newlink: '%s'", url)



	def processImageLink(self, url, baseUrl):


		print("Image tag search", url)

		# Skip tags with `img src=""`.
		# No idea why they're there, but they are
		if not url:
			return

		# Filter by domain
		if not self.allImages and not any([base in url for base in self._fileDomains]):
			return

		# and by blocked words
		hadbad = False
		for badword in self._badwords:
			if badword in url:
				hadbad = True
		if hadbad:
			return
		print("Image tag search", url)


		# upsert for `url`. Do not reset dlstate to avoid re-transferring binary files.
		url = self.urlClean(url)

		return self.processNewUrl(url, baseUrl=baseUrl, istext=False)


	def extractLinks(self, soup, baseUrl):
		# All links have been resolved to fully-qualified paths at this point.

		ret = []
		for (dummy_isImg, tag, attr) in urlContainingTargets:

			for link in soup.findAll(tag):


				# Skip empty anchor tags
				try:
					url = link[attr]
				except KeyError:
					continue


				item = self.processLinkItem(url, baseUrl)
				if item:
					ret.append(item)

		return ret


	def extractImages(self, soup, baseUrl):
		ret = []
		for imtag in soup.find_all("img"):
						# Skip empty anchor tags
			try:
				url = imtag["src"]
			except KeyError:
				continue

			item = self.processImageLink(url, baseUrl)
			if item:
				ret.append(item)
		return ret


	def convertToReaderImage(self, inStr):
		inStr = self.urlClean(inStr)
		return self.convertToReaderUrl(inStr)

	def relink(self, soup, imRelink=None):
		# The google doc reader relinking mechanisms requires overriding the
		# image relinking mechanism. As such, allow that to be overridden
		# if needed

		if not imRelink:
			imRelink = self.convertToReaderImage


		for (isImg, tag, attr) in urlContainingTargets:

			if not isImg:
				for link in soup.findAll(tag):
					try:
						if self.checkRelinkDomain(link[attr]):
							link[attr] = self.convertToReaderUrl(link[attr])
					except KeyError:
						continue

			else:
				for link in soup.findAll(tag):
					try:
						link[attr] = imRelink(link[attr])

						if tag == 'img':
							# Force images that are oversize to fit the window.
							link["style"] = 'max-width: 95%;'

							if 'width' in link.attrs:
								del link.attrs['width']
							if 'height' in link.attrs:
								del link.attrs['height']

					except KeyError:
						continue

		return soup





	def canonizeUrls(self, soup, pageUrl):
		self.log.info("Making all links on page absolute.")

		for (dummy_isimg, tag, attr) in urlContainingTargets:
			for link in soup.findAll(tag):
				try:
					url = link[attr]
				except KeyError:
					pass
				else:
					link[attr] = rebaseUrl(url, pageUrl)
					if link[attr] != url:
						self.log.debug("Changed URL from '%s' to '%s'", url, link[attr])
		return soup


	def decomposeItems(self, soup, toDecompose):
		# Decompose all the parts we don't want
		for key in toDecompose:
			for instance in soup.find_all(True, attrs=key):

				# So.... yeah. At least one blogspot site has EVERY class used in the
				# <body> tag, for no coherent reason. Therefore, *never* decompose the <body>
				# tag, even if it has a bad class in it.
				if instance.name == 'body':
					continue

				instance.decompose() # This call permutes the tree!

		return soup

	def decomposeAdditional(self, soup):

		# Clear out all the iframes
		for instance in soup.find_all('iframe'):
			instance.decompose()

		# Clean out any local stylesheets
		for instance in soup.find_all('style'):
			instance.decompose()

		return soup

	def cleanHtmlPage(self, srcSoup, url=None):

		# since readability strips tag attributes, we preparse with BS4,
		# parse with readability, and then do reformatting *again* with BS4
		# Yes, this is ridiculous.

		ctnt = srcSoup.prettify()
		doc = readability.readability.Document(ctnt)
		doc.parse()
		content = doc.content()

		soup = bs4.BeautifulSoup(content)
		soup = self.relink(soup)
		contents = ''



		# Since the content we're extracting will be embedded into another page, we want to
		# strip out the <body> and <html> tags. `unwrap()`  replaces the soup with the contents of the
		# tag it's called on. We end up with just the contents of the <body> tag.
		soup.body.unwrap()
		contents = soup.prettify()

		title = self.extractTitle(soup, doc, url)

		if isinstance(self.stripTitle, (list, set)):
			for stripTitle in self.stripTitle:
				title = title.replace(stripTitle, "")
		else:
			title = title.replace(self.stripTitle, "")

		title = title.strip()
		return title, contents

	# Methods to allow the child-class to modify the content at various points.
	def extractTitle(self, srcSoup, doc, url):
		title = doc.title()
		return title

	def postprocessBody(self, soup):
		return soup

	def preprocessBody(self, soup):
		return soup



	def processNewUrl(self, url, baseUrl=None, istext=True):
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
		return url




	# Process a plain HTML page.
	# This call does a set of operations to permute and clean a HTML page.
	#
	# First, it decomposes all tags with attributes dictated in the `_decomposeBefore` class variable
	# it then canonizes all the URLs on the page, extracts all the URLs from the page,
	# then decomposes all the tags in the `decompose` class variable, feeds the content through
	# readability, and finally saves the processed HTML into the database
	def extractContent(self):
		self.log.info("Processing '%s' as HTML.", self.pageUrl)
		soup = bs4.BeautifulSoup(self.content)


		# Allow child-class hooking
		soup = self.preprocessBody(soup)

		# Clear out any particularly obnoxious content before doing any parsing.
		soup = self.decomposeItems(soup, self._decomposeBefore)

		# Make all the page URLs fully qualified, so they're unambiguous
		soup = self.canonizeUrls(soup, self.pageUrl)

		# Conditionally pull out the page content and enqueue it.
		if self.checkDomain(self.pageUrl):
			plainLinks = self.extractLinks(soup, self.pageUrl)
			imageLinks = self.extractImages(soup, self.pageUrl)
		else:
			self.log.warn("Not extracting images or links for url '%s'", self.pageUrl)
			plainLinks = []
			imageLinks = []

		# Do the later cleanup to prep the content for local rendering.
		soup = self.decomposeItems(soup, self._decompose)

		soup = self.decomposeAdditional(soup)

		# Allow child-class hooking
		soup = self.postprocessBody(soup)

		# Process page with readability, extract title.
		pgTitle, pgBody = self.cleanHtmlPage(soup, url=self.pageUrl)
		self.log.info("Page with title '%s' retreived.", pgTitle)

		ret = {}
		ret['fLinks']   = plainLinks
		ret['iLinks']   = imageLinks
		ret['title']    = pgTitle
		ret['contents'] = pgBody


		return ret

		# self.updateDbEntry(url=url, title=pgTitle, contents=pgBody, mimetype=mimeType, dlstate=2)






if __name__ == "__main__":
	print("Test mode!")
	import webFunctions
	import logSetup
	logSetup.initLogging()

	wg = webFunctions.WebGetRobust()
	content = wg.getpage('http://www.arstechnica.com')
	scraper = HtmlPageProcessor(['http://www.arstechnica.com', "http://cdn.arstechnica.com/"], 'http://www.arstechnica.com', content, 'Main.Test', tld=['com', 'net'])
	print(scraper)
	extr = scraper.extractContent()
	print(extr['iLinks'])
	# print(extr['fLinks'])

