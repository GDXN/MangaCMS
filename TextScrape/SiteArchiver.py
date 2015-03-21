


import runStatus
runStatus.preloadDicts = False

# import Levenshtein as lv

import abc
import urllib.parse
import TextScrape.RelinkLookup
import LogBase

# import sql.operators as sqlo

import inspect
import collections
import traceback
import time
import queue
import bs4
import TextScrape.urlFuncs
from concurrent.futures import ThreadPoolExecutor

import TextScrape.TextDbBase
import TextScrape.HtmlProcessor

import os.path
import os
import settings
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


class SiteArchiver(TextScrape.TextDbBase.TextDbBase, LogBase.LoggerMixin, metaclass=abc.ABCMeta):

	# Abstract class (must be subclassed)
	__metaclass__ = abc.ABCMeta

	plugin_type = 'SiteArchiver'

	validKwargs = []

	tableName       = "book_items"
	changeTableName = "book_changes"

	threads = 2

	QUERY_DEBUG = False
	IGNORE_MALFORMED_URLS = False
	FOLLOW_GOOGLE_LINKS = True

	# Fetch items up to 2^30 links away from the root source
	# This (functionally) equates to no limit.
	# The db defaults to (2^31)-1 (e.g. max signed integer value) anyways
	FETCH_DISTANCE = 2**30


	@abc.abstractproperty
	def pluginName(self):
		pass

	@abc.abstractproperty
	def loggerPath(self):
		pass

	@abc.abstractproperty
	def tableKey(self):
		pass

	@abc.abstractproperty
	def baseUrl(self):
		pass
	@abc.abstractproperty
	def startUrl(self):
		pass

	@abc.abstractproperty
	def badwords(self):
		pass

	procClass = TextScrape.HtmlProcessor.HtmlPageProcessor

	tld             = []
	decomposeBefore = []
	decompose       = []
	fileDomains     = []
	allImages       = True

	stripTitle = ''

	def __init__(self):
		super().__init__()
		self.newLinkQueue = queue.Queue()

		self.loadFilters()


	def loadFilters(self):
		# This is a (slightly confusing) function that does some metaclass hijinks.
		# Basically, I want to get the instance of the named variables in `collapse` from
		# *each* class in the inheritence chain, and consolidate them all into a single
		# list. Therefore, I walk the inheritence chain, and extract them from each separate
		# class therein.

		self.log.info("Collapsing inheritance chains.")
		collapse = [
			('tld',             self.tld),
			('decomposeBefore', self.decomposeBefore),
			('decompose',       self.decompose),
			('fileDomains',     self.fileDomains),
			('badwords',        self.badwords),
		]

		for cls in inspect.getmro(type(self)):
			for name, moveto in collapse:
				if hasattr(cls, name):
					item = getattr(cls, name)
					if isinstance(item, collections.Iterable):
						for item in item:
							# Only copy dicts and strings (if we copy lists, we'll get a self-refferential list)
							# if we copy everything, it'll also insert the abstract base class member.
							if isinstance(item, (dict, str)):
								if not item in moveto:

									# Either add item (for sets) or append (for lists)
									if isinstance(moveto, set):
										moveto.add(item)
									elif isinstance(moveto, list):
										moveto.append(item)
									else:
										raise ValueError("Don't know how to append to item: '%s', type '%s'" % (moveto, type(moveto)))

							else:
								print(item)


	########################################################################################################################
	#
	#	########  ####  ######  ########     ###    ########  ######  ##     ##    ##     ## ######## ######## ##     ##  #######  ########   ######
	#	##     ##  ##  ##    ## ##     ##   ## ##      ##    ##    ## ##     ##    ###   ### ##          ##    ##     ## ##     ## ##     ## ##    ##
	#	##     ##  ##  ##       ##     ##  ##   ##     ##    ##       ##     ##    #### #### ##          ##    ##     ## ##     ## ##     ## ##
	#	##     ##  ##   ######  ########  ##     ##    ##    ##       #########    ## ### ## ######      ##    ######### ##     ## ##     ##  ######
	#	##     ##  ##        ## ##        #########    ##    ##       ##     ##    ##     ## ##          ##    ##     ## ##     ## ##     ##       ##
	#	##     ##  ##  ##    ## ##        ##     ##    ##    ##    ## ##     ##    ##     ## ##          ##    ##     ## ##     ## ##     ## ##    ##
	#	########  ####  ######  ##        ##     ##    ##     ######  ##     ##    ##     ## ########    ##    ##     ##  #######  ########   ######
	#
	########################################################################################################################

	def getEmptyRet(self):
		return {'plainLinks' : [], 'rsrcLinks' : []}



	def processHtmlPage(self, url, content):
		scraper = self.procClass(
									baseUrls        = self.baseUrl,
									pageUrl         = url,
									pgContent       = content,
									loggerPath      = self.loggerPath,
									badwords        = self.badwords,
									decompose       = self.decompose,
									decomposeBefore = self.decomposeBefore,
									fileDomains     = self.fileDomains,
									allImages       = self.allImages,
									followGLinks    = self.FOLLOW_GOOGLE_LINKS,
									ignoreBadLinks  = self.IGNORE_MALFORMED_URLS,
									tld             = self.tld,
									stripTitle      = self.stripTitle
								)
		extracted = scraper.extractContent()

		return extracted

	def processAsMarkdown(self, url, content):
		raise NotImplementedError("TODO: FIX ME!")
	def extractGoogleDriveFolder(self, url):
		raise NotImplementedError("TODO: FIX ME!")
	def retreiveGoogleDoc(self, url):
		raise NotImplementedError("TODO: FIX ME!")
	def retreiveGoogleFile(self, url):
		raise NotImplementedError("TODO: FIX ME!")



	########################################################################################################################
	#
	#	##     ## #### ##     ## ########         ######## ##    ## ########  ########
	#	###   ###  ##  ###   ### ##                  ##     ##  ##  ##     ## ##
	#	#### ####  ##  #### #### ##                  ##      ####   ##     ## ##
	#	## ### ##  ##  ## ### ## ######   #######    ##       ##    ########  ######
	#	##     ##  ##  ##     ## ##                  ##       ##    ##        ##
	#	##     ##  ##  ##     ## ##                  ##       ##    ##        ##
	#	##     ## #### ##     ## ########            ##       ##    ##        ########
	#
	#	########  ####  ######  ########     ###    ########  ######  ##     ## ######## ########
	#	##     ##  ##  ##    ## ##     ##   ## ##      ##    ##    ## ##     ## ##       ##     ##
	#	##     ##  ##  ##       ##     ##  ##   ##     ##    ##       ##     ## ##       ##     ##
	#	##     ##  ##   ######  ########  ##     ##    ##    ##       ######### ######   ########
	#	##     ##  ##        ## ##        #########    ##    ##       ##     ## ##       ##   ##
	#	##     ##  ##  ##    ## ##        ##     ##    ##    ##    ## ##     ## ##       ##    ##
	#	########  ####  ######  ##        ##     ##    ##     ######  ##     ## ######## ##     ##
	#
	########################################################################################################################



	def dispatchContent(self, url, content, fName, mimeType):
		self.log.info("Dispatching file '%s' with mime-type '%s'", fName, mimeType)

		if mimeType in ['text/xml', 'text/atom+xml', 'application/xml']:
			self.log.info("XML File?")
			self.log.info("URL: '%s'", url)
			self.updateDbEntry(url=url, title='', contents=content, mimetype=mimeType, dlstate=2, istext=True)
			return self.getEmptyRet()



		elif mimeType in ['text/css']:
			self.log.info("CSS!")
			self.log.info("URL: '%s'", url)
			self.updateDbEntry(url=url, title='', contents=content, mimetype=mimeType, dlstate=2, istext=True)
			return self.getEmptyRet()

		elif mimeType in ['application/x-javascript', 'application/javascript']:
			self.log.info("Javascript Resource!")
			self.log.info("URL: '%s'", url)
			self.updateDbEntry(url=url, title='', contents=content, mimetype=mimeType, dlstate=2, istext=True)
			return self.getEmptyRet()

		elif mimeType in ["image/gif", "image/jpeg", "image/pjpeg", "image/png", "image/svg+xml", "image/vnd.djvu"]:
			self.log.info("Processing '%s' as an image file.", url)
			self.saveFile(url, mimeType, fName, content)
			return self.getEmptyRet()

		elif mimeType in ["application/octet-stream", "application/x-mobipocket-ebook", "application/pdf", "application/zip"]:
			self.log.info("Processing '%s' as an binary file.", url)
			self.saveFile(url, mimeType, fName, content)
			return self.getEmptyRet()


		elif mimeType == 'text/html':
			ret = self.processHtmlPage(url, content)

		elif mimeType in ['text/plain']:
			ret = self.processAsMarkdown(url, content)

		else:
			self.log.error("Unknown MIME Type: '%s', Url: '%s'", mimeType, url)
			self.log.error("Not saving file!")
			return self.getEmptyRet()


		self.updateDbEntry(url=url, title=ret['title'], contents=ret['contents'], mimetype='text/html', dlstate=2, istext=True)

		return ret

	def retreivePlainResource(self, url):
		self.log.info("Fetching Simple Resource: '%s'", url)
		try:
			content, fName, mimeType = self.getItem(url)
		except ValueError:

			for line in traceback.format_exc().split("\n"):
				self.log.critical(line)
			self.upsert(url, dlstate=-1, contents='Error downloading!')
			return self.getEmptyRet()

		return self.dispatchContent(url, content, fName, mimeType)



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


	def processResponse(self, response, distance):
		plain = set(response['plainLinks'])
		resource = set(response['rsrcLinks'])

		for link in plain:
			self.newLinkQueue.put((link, True, distance+1))

		for link in resource:
			self.newLinkQueue.put((link, False, distance+1))




	def getFilenameFromIdName(self, rowid, filename):
		if not os.path.exists(settings.bookCachePath):
			self.log.warn("Cache directory for book items did not exist. Creating")
			self.log.warn("Directory at path '%s'", settings.bookCachePath)
			os.makedirs(settings.bookCachePath)

		# one new directory per 1000 items.
		dirName = '%s' % (rowid // 1000)
		dirPath = os.path.join(settings.bookCachePath, dirName)
		if not os.path.exists(dirPath):
			os.mkdir(dirPath)

		filename = 'ID%s - %s' % (rowid, filename)
		filename = nameTools.makeFilenameSafe(filename)
		fqpath = os.path.join(dirPath, filename)

		return fqpath




	########################################################################################################################
	#
	#	########    ###     ######  ##    ##    ########  ####  ######  ########     ###    ########  ######  ##     ## ######## ########
	#	   ##      ## ##   ##    ## ##   ##     ##     ##  ##  ##    ## ##     ##   ## ##      ##    ##    ## ##     ## ##       ##     ##
	#	   ##     ##   ##  ##       ##  ##      ##     ##  ##  ##       ##     ##  ##   ##     ##    ##       ##     ## ##       ##     ##
	#	   ##    ##     ##  ######  #####       ##     ##  ##   ######  ########  ##     ##    ##    ##       ######### ######   ########
	#	   ##    #########       ## ##  ##      ##     ##  ##        ## ##        #########    ##    ##       ##     ## ##       ##   ##
	#	   ##    ##     ## ##    ## ##   ##     ##     ##  ##  ##    ## ##        ##     ##    ##    ##    ## ##     ## ##       ##    ##
	#	   ##    ##     ##  ######  ##    ##    ########  ####  ######  ##        ##     ##    ##     ######  ##     ## ######## ##     ##
	#
	########################################################################################################################

	# This is the main function that's called by the task management system.
	# Retreive remote content at `url`, call the appropriate handler for the
	# transferred content (e.g. is it an image/html page/binary file)
	def dispatchUrlRequest(self, url, pageDistance):

		url = TextScrape.urlFuncs.urlClean(url)
		# Snip off leading slashes that have shown up a few times.
		if url.startswith("//"):
			url = 'http://'+url[2:]

		# print('Dispatch URL', url)

		netloc = urllib.parse.urlsplit(url.lower()).netloc

		isGdoc, realUrl = gdp.isGdocUrl(url)
		isGfile, fileUrl = gdp.isGFileUrl(url)

			# print('Fetching: ', url, 'distance', pageDistance)
			# print(isGdoc, isGfile)
		if 'drive.google.com' in netloc:
			self.log.info("Google Drive content!")
			response = self.extractGoogleDriveFolder(url)
		elif isGdoc:
			self.log.info("Google Docs content!")
			response = self.retreiveGoogleDoc(realUrl)
		elif isGfile:
			self.log.info("Google File content!")
			response = self.retreiveGoogleFile(realUrl)

		else:
			response = self.retreivePlainResource(url)

		self.processResponse(response, pageDistance)

	########################################################################################################################
	#
	#	########  ########   #######   ######  ########  ######   ######      ######   #######  ##    ## ######## ########   #######  ##
	#	##     ## ##     ## ##     ## ##    ## ##       ##    ## ##    ##    ##    ## ##     ## ###   ##    ##    ##     ## ##     ## ##
	#	##     ## ##     ## ##     ## ##       ##       ##       ##          ##       ##     ## ####  ##    ##    ##     ## ##     ## ##
	#	########  ########  ##     ## ##       ######    ######   ######     ##       ##     ## ## ## ##    ##    ########  ##     ## ##
	#	##        ##   ##   ##     ## ##       ##             ##       ##    ##       ##     ## ##  ####    ##    ##   ##   ##     ## ##
	#	##        ##    ##  ##     ## ##    ## ##       ##    ## ##    ##    ##    ## ##     ## ##   ###    ##    ##    ##  ##     ## ##
	#	##        ##     ##  #######   ######  ########  ######   ######      ######   #######  ##    ##    ##    ##     ##  #######  ########
	#
	########################################################################################################################

	def queueLoop(self):
		self.log.info("Fetch thread starting")

		# Timeouts is used to track when queues are empty
		# Since I have multiple threads, and there are known
		# situations where we can be certain that there will be
		# only one request (such as at startup), we need to
		# have a mechanism for retrying fetches from a queue a few
		# times before concluding there is nothing left to do
		timeouts = 0
		while runStatus.run:
			try:
				newTodo = self.getToDo(self.FETCH_DISTANCE)
				if newTodo:
					url, distance = newTodo
					try:
						self.dispatchUrlRequest(url, distance)
					except urllib.error.URLError:
						content = "DOWNLOAD FAILED"
						content += "<br>"
						content += traceback.format_exc()
						self.upsert(url, dlstate=-1, contents=content, distance=distance)
					except DownloadException:
						content = "DOWNLOAD FAILED"
						content += "<br>"
						content += traceback.format_exc()
						self.upsert(url, dlstate=-1, contents=content, distance=distance)


				else:
					timeouts += 1
					time.sleep(1)
					self.log.info("Fetch task waiting.")

				if timeouts > 5:
					break

			except Exception:
				traceback.print_exc()
		self.log.info("Fetch thread exiting!")

	def crawl(self):

		self.resetStuckItems()

		if hasattr(self, 'preFlight'):
			self.preFlight()

		haveUrls = set()
		if isinstance(self.startUrl, (list, set)):
			for url in self.startUrl:
				self.log.info("Start URL: '%s'", url)
				self.upsert(url, dlstate=0, distance=0)
		else:
			self.upsert(self.startUrl, dlstate=0, distance=0)

		with ThreadPoolExecutor(max_workers=self.threads) as executor:

			processes = []
			for dummy_x in range(self.threads):
				self.log.info("Starting child-thread!")
				processes.append(executor.submit(self.queueLoop))


			todoIntegrator = time.time()
			printInterval = 15  # Print items in queue every 10 seconds
			while runStatus.run:

				# Every 15 seconds, print how many items remain todo.
				if time.time() > (todoIntegrator + printInterval):
					self.log.info("Items remaining in todo queue: %s", self.getTodoCount())
					todoIntegrator += printInterval

				try:
					got = self.newLinkQueue.get_nowait()
					if not got:
						continue
					if len(got) == 3:
						url, istext, distance = got
						if not url in haveUrls:

							if url.lower().startswith('http'):
								self.log.info("New URL: '%s', distance: %s", url, distance)

								# Only reset the downloadstate for content, not
								# resources
								if istext:
									self.upsert(url, istext=istext, dlstate=0, distance=distance)
								else:
									self.upsert(url, istext=istext, distance=distance)
								haveUrls.add(url)
							else:
								raise ValueError("Invalid URL added: '%s'", got)
					else:
						raise ValueError("Data from queue is not a 2-tuple? '%s'" % got)

				except queue.Empty:
					time.sleep(0.01)




				if not any([proc.running() for proc in processes]):
					self.log.info("All threads stopped. Main thread exiting.")
					break
			if not runStatus.run:
				self.log.warn("Execution stopped because of user-interrupt!")

		self.log.info("Crawler scanned a total of '%s' pages", len(haveUrls))
		self.log.info("Queue Feeder thread exiting!")


if __name__ == "__main__":
	print("Test mode!")
	domains = TextScrape.RelinkLookup.fetchRelinkableDomains()
	print(domains)
	print(SiteArchiver)

