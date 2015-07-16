

if __name__ == "__main__":
	import logSetup
	logSetup.initLogging()

import WebMirror.rules
import LogBase

# import urllib.parse
# import sql.operators as sqlo

# import inspect
# import collections
# import traceback
# import time
# import queue
# import bs4
# import TextScrape.urlFuncs
# from concurrent.futures import ThreadPoolExecutor


# import os.path
# import os

# import TextScrape.gDocParse as gdp

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


class SiteArchiver(LogBase.LoggerMixin):


	loggerPath = "Main.SiteArchiver"

	threads = 2

	# Fetch items up to 1,000,000 (1 million) links away from the root source
	# This (functionally) equates to no limit.
	# The db defaults to  (e.g. max signed integer value) anyways
	FETCH_DISTANCE = 1000 * 1000

	def __init__(self):
		super().__init__()

		self.ruleset = WebMirror.rules.get_rules()

		self.relinkable = set()
		for item in self.ruleset:
			[self.relinkable.add(url) for url in item['fileDomains']]
			[self.relinkable.add(url) for url in item['netlocs']]


	########################################################################################################################



	########################################################################################################################
	#
	#	########  ####  ######  ########     ###    ########  ######  ##     ##      ##     ## ######## ######## ##     ##  #######  ########   ######
	#	##     ##  ##  ##    ## ##     ##   ## ##      ##    ##    ## ##     ##      ###   ### ##          ##    ##     ## ##     ## ##     ## ##    ##
	#	##     ##  ##  ##       ##     ##  ##   ##     ##    ##       ##     ##      #### #### ##          ##    ##     ## ##     ## ##     ## ##
	#	##     ##  ##   ######  ########  ##     ##    ##    ##       #########      ## ### ## ######      ##    ######### ##     ## ##     ##  ######
	#	##     ##  ##        ## ##        #########    ##    ##       ##     ##      ##     ## ##          ##    ##     ## ##     ## ##     ##       ##
	#	##     ##  ##  ##    ## ##        ##     ##    ##    ##    ## ##     ##      ##     ## ##          ##    ##     ## ##     ## ##     ## ##    ##
	#	########  ####  ######  ##        ##     ##    ##     ######  ##     ##      ##     ## ########    ##    ##     ##  #######  ########   ######
	#
	########################################################################################################################

# 	def getEmptyRet(self):
# 		return {'plainLinks' : [], 'rsrcLinks' : []}


# 	def processReturnedFileResources(self, resources):

# 		# fMap = {}


# 		for fName, mimeType, content, fHash in resources:
# 			# m = hashlib.md5()
# 			# m.update(content)
# 			# fHash = m.hexdigest()

# 			hashName = self.tableKey+fHash

# 			# fMap[fName] = fHash

# 			fName = os.path.split(fName)[-1]

# 			self.log.info("Resource = '%s', '%s', '%s'", fName, mimeType, hashName)
# 			if mimeType in ["image/gif", "image/jpeg", "image/pjpeg", "image/png", "image/svg+xml", "image/vnd.djvu"]:
# 				self.log.info("Processing resource '%s' as an image file. (mimetype: %s)", fName, mimeType)
# 				self.upsert(hashName, istext=False)
# 				self.saveFile(hashName, mimeType, fName, content)
# 			elif mimeType in ["application/octet-stream"]:
# 				self.log.info("Processing '%s' as an binary file.", fName)
# 				self.upsert(hashName, istext=False)
# 				self.saveFile(hashName, mimeType, fName, content)
# 			else:
# 				self.log.warn("Unknown MIME Type? '%s', FileName: '%s'", mimeType, fName)

# 		if len(resources) == 0:
# 			self.log.info("File had no resource content!")




# 	def processHtmlPage(self, url, content):
# 		scraper = self.htmlProcClass(
# 									baseUrls        = self.baseUrl,
# 									pageUrl         = url,
# 									pgContent       = content,
# 									loggerPath      = self.loggerPath,
# 									badwords        = self.badwords,
# 									decompose       = self.decompose,
# 									decomposeBefore = self.decomposeBefore,
# 									fileDomains     = self.fileDomains,
# 									allImages       = self.allImages,
# 									followGLinks    = self.FOLLOW_GOOGLE_LINKS,
# 									ignoreBadLinks  = self.IGNORE_MALFORMED_URLS,
# 									tld             = self.tld,
# 									stripTitle      = self.stripTitle,
# 									relinkable      = self.relinkable
# 								)
# 		extracted = scraper.extractContent()

# 		return extracted


# 	def extractGoogleDriveFolder(self, url):
# 		scraper = self.gdriveClass(
# 									pageUrl         = url,
# 									loggerPath      = self.loggerPath,
# 									relinkable      = self.relinkable
# 								)
# 		extracted = scraper.extractContent()

# 		return extracted

# 	def retreiveGoogleDoc(self, url):
# 		# pageUrl, loggerPath, tableKey, scannedDomains=None, tlds=None

# 		try:
# 			scraper = self.gDocClass(
# 										pageUrl         = url,
# 										loggerPath      = self.loggerPath,
# 										tableKey        = self.tableKey,
# 										scannedDomains  = self.baseUrl,
# 										tlds            = self.tld,
# 										relinkable      = self.relinkable
# 									)
# 			extracted, resources = scraper.extractContent()
# 			self.processReturnedFileResources(resources)
# 		except TextScrape.gDocParse.CannotAccessGDocException:
# 			self.log.warning("Cannot access google doc content. Attempting to access as a plain HTML resource via /pub interface")
# 			url = url + "/pub"
# 			extracted = self.retreivePlainResource(url)
# 			if "This document is not published." in extracted['contents']:
# 				raise ValueError("Could not extract google document!")

# 		return extracted

# 	def processAsMarkdown(self, url, content):
# 		pbLut = getattr(self, 'pasteBinLut', {})

# 		scraper = self.markdownClass(
# 									pageUrl         = url,
# 									loggerPath      = self.loggerPath,
# 									content         = content,
# 									pbLut           = pbLut
# 								)
# 		extracted = scraper.extractContent()

# 		return extracted

# 	def retreiveGoogleFile(self, url):


# 		self.log.info("Should fetch google file at '%s'", url)
# 		doc = gdp.GFileExtractor(url)

# 		attempts = 0

# 		while 1:
# 			attempts += 1
# 			try:
# 				content, fName, mType = doc.extract()
# 			except TypeError:
# 				self.log.critical('Extracting item failed!')
# 				for line in traceback.format_exc().strip().split("\n"):
# 					self.log.critical(line.strip())
# 				return self.getEmptyRet()
# 			if content:
# 				break
# 			if attempts > 3:
# 				raise DownloadException


# 			self.log.error("No content? Retrying!")

# 		scraper = self.htmlProcClass(
# 									baseUrls        = self.baseUrl,
# 									pageUrl         = url,
# 									pgContent       = content,
# 									loggerPath      = self.loggerPath,
# 									badwords        = self.badwords,
# 									decompose       = self.decompose,
# 									decomposeBefore = self.decomposeBefore,
# 									fileDomains     = self.fileDomains,
# 									allImages       = self.allImages,
# 									followGLinks    = self.FOLLOW_GOOGLE_LINKS,
# 									ignoreBadLinks  = self.IGNORE_MALFORMED_URLS,
# 									tld             = self.tld,
# 									stripTitle      = self.stripTitle
# 								)
# 		extracted = scraper.extractContent()

# 		return extracted


# 		raise NotImplementedError("TODO: FIX ME!")



# 	########################################################################################################################
# 	#
# 	#	##     ## #### ##     ## ########         ######## ##    ## ########  ########
# 	#	###   ###  ##  ###   ### ##                  ##     ##  ##  ##     ## ##
# 	#	#### ####  ##  #### #### ##                  ##      ####   ##     ## ##
# 	#	## ### ##  ##  ## ### ## ######   #######    ##       ##    ########  ######
# 	#	##     ##  ##  ##     ## ##                  ##       ##    ##        ##
# 	#	##     ##  ##  ##     ## ##                  ##       ##    ##        ##
# 	#	##     ## #### ##     ## ########            ##       ##    ##        ########
# 	#
# 	#	########  ####  ######  ########     ###    ########  ######  ##     ## ######## ########
# 	#	##     ##  ##  ##    ## ##     ##   ## ##      ##    ##    ## ##     ## ##       ##     ##
# 	#	##     ##  ##  ##       ##     ##  ##   ##     ##    ##       ##     ## ##       ##     ##
# 	#	##     ##  ##   ######  ########  ##     ##    ##    ##       ######### ######   ########
# 	#	##     ##  ##        ## ##        #########    ##    ##       ##     ## ##       ##   ##
# 	#	##     ##  ##  ##    ## ##        ##     ##    ##    ##    ## ##     ## ##       ##    ##
# 	#	########  ####  ######  ##        ##     ##    ##     ######  ##     ## ######## ##     ##
# 	#
# 	########################################################################################################################



# 	def dispatchContent(self, url, content, fName, mimeType):
# 		self.log.info("Dispatching file '%s' with mime-type '%s'", fName, mimeType)

# 		# *sigh*. So minus.com is fucking up their http headers, and apparently urlencoding the
# 		# mime type, because apparently they're shit at things.
# 		# Anyways, fix that.
# 		if '%2F' in  mimeType:
# 			mimeType = mimeType.replace('%2F', '/')

# 		if mimeType in ['text/xml', 'text/atom+xml', 'application/atom+xml', 'application/xml']:
# 			self.log.info("XML File?")
# 			self.log.info("URL: '%s'", url)
# 			self.updateDbEntry(url=url, title='', contents=content, mimetype=mimeType, dlstate=2, istext=True)
# 			return self.getEmptyRet()

# 		elif mimeType in ['text/css']:
# 			self.log.info("CSS!")
# 			self.log.info("URL: '%s'", url)
# 			self.updateDbEntry(url=url, title='', contents=content, mimetype=mimeType, dlstate=2, istext=True)
# 			return self.getEmptyRet()

# 		elif mimeType in ['application/x-javascript', 'application/javascript']:
# 			self.log.info("Javascript Resource!")
# 			self.log.info("URL: '%s'", url)
# 			self.updateDbEntry(url=url, title='', contents=content, mimetype=mimeType, dlstate=2, istext=True)
# 			return self.getEmptyRet()

# 		elif mimeType in ["image/gif", "image/jpeg", "image/pjpeg", "image/png", "image/svg+xml", "image/vnd.djvu"]:
# 			self.log.info("Processing '%s' as an image file.", url)
# 			self.saveFile(url, mimeType, fName, content)
# 			return self.getEmptyRet()

# 		elif mimeType in ["application/octet-stream", "application/x-mobipocket-ebook", "application/pdf", "application/zip"]:
# 			self.log.info("Processing '%s' as an binary file.", url)
# 			self.saveFile(url, mimeType, fName, content)
# 			return self.getEmptyRet()


# 		elif mimeType == 'text/html':
# 			ret = self.processHtmlPage(url, content)

# 		elif mimeType in ['text/plain']:
# 			ret = self.processAsMarkdown(url, content)

# 		else:
# 			self.log.error("Unknown MIME Type: '%s', Url: '%s'", mimeType, url)
# 			self.log.error("Not saving file!")
# 			return self.getEmptyRet()


# 		return ret




# 	def getItem(self, itemUrl):

# 		try:
# 			content, handle = self.wg.getpage(itemUrl, returnMultiple=True)
# 		except:
# 			if self.cloudflare:
# 				if not self.wg.stepThroughCloudFlare(itemUrl, titleNotContains='Just a moment...'):
# 					raise ValueError("Could not step through cloudflare!")
# 				# Cloudflare cookie set, retrieve again
# 				content, handle = self.wg.getpage(itemUrl, returnMultiple=True)
# 			else:
# 				raise



# 		if not content or not handle:
# 			raise ValueError("Failed to retreive file from page '%s'!" % itemUrl)

# 		fileN = urllib.parse.unquote(urllib.parse.urlparse(handle.geturl())[2].split("/")[-1])
# 		fileN = bs4.UnicodeDammit(fileN).unicode_markup
# 		mType = handle.info()['Content-Type']

# 		# If there is an encoding in the content-type (or any other info), strip it out.
# 		# We don't care about the encoding, since WebFunctions will already have handled that,
# 		# and returned a decoded unicode object.

# 		if mType and ";" in mType:
# 			mType = mType.split(";")[0].strip()


# 		self.log.info("Retreived file of type '%s', name of '%s' with a size of %0.3f K", mType, fileN, len(content)/1000.0)
# 		return content, fileN, mType


# 	def retreivePlainResource(self, url):
# 		self.log.info("Fetching Simple Resource: '%s'", url)
# 		try:
# 			content, fName, mimeType = self.getItem(url)
# 		except ValueError:

# 			for line in traceback.format_exc().split("\n"):
# 				self.log.critical(line)
# 			self.upsert(url, dlstate=-1, contents='Error downloading!')
# 			return self.getEmptyRet()

# 		return self.dispatchContent(url, content, fName, mimeType)






# 	########################################################################################################################
# 	#
# 	#	########    ###     ######  ##    ##    ########  ####  ######  ########     ###    ########  ######  ##     ## ######## ########
# 	#	   ##      ## ##   ##    ## ##   ##     ##     ##  ##  ##    ## ##     ##   ## ##      ##    ##    ## ##     ## ##       ##     ##
# 	#	   ##     ##   ##  ##       ##  ##      ##     ##  ##  ##       ##     ##  ##   ##     ##    ##       ##     ## ##       ##     ##
# 	#	   ##    ##     ##  ######  #####       ##     ##  ##   ######  ########  ##     ##    ##    ##       ######### ######   ########
# 	#	   ##    #########       ## ##  ##      ##     ##  ##        ## ##        #########    ##    ##       ##     ## ##       ##   ##
# 	#	   ##    ##     ## ##    ## ##   ##     ##     ##  ##  ##    ## ##        ##     ##    ##    ##    ## ##     ## ##       ##    ##
# 	#	   ##    ##     ##  ######  ##    ##    ########  ####  ######  ##        ##     ##    ##     ######  ##     ## ######## ##     ##
# 	#
# 	########################################################################################################################

# 	# This is the main function that's called by the task management system.
# 	# Retreive remote content at `url`, call the appropriate handler for the
# 	# transferred content (e.g. is it an image/html page/binary file)
# 	def dispatchUrlRequest(self, url, pageDistance):

# 		url = TextScrape.urlFuncs.urlClean(url)
# 		# Snip off leading slashes that have shown up a few times.
# 		if url.startswith("//"):
# 			url = 'http://'+url[2:]

# 		# print('Dispatch URL', url)

# 		netloc = urllib.parse.urlsplit(url.lower()).netloc

# 		isGdoc, realUrl = gdp.isGdocUrl(url)
# 		isGfile, fileUrl = gdp.isGFileUrl(url)

# 			# print('Fetching: ', url, 'distance', pageDistance)
# 			# print(isGdoc, isGfile)
# 		if 'drive.google.com' in netloc:
# 			self.log.info("Google Drive content!")
# 			response = self.extractGoogleDriveFolder(url)
# 		elif isGdoc:
# 			self.log.info("Google Docs content!")
# 			response = self.retreiveGoogleDoc(realUrl)
# 		elif isGfile:
# 			self.log.info("Google File content!")
# 			response = self.retreiveGoogleFile(realUrl)

# 		else:
# 			response = self.retreivePlainResource(url)

# 		if 'title' in response and 'contents' in response:
# 			self.updateDbEntry(url=url, title=response['title'], contents=response['contents'], mimetype='text/html', dlstate=2, istext=True)

# 		self.processResponse(response, pageDistance)


# 	def processResponse(self, response, distance):
# 		plain = set(response['plainLinks'])
# 		resource = set(response['rsrcLinks'])

# 		for link in plain:
# 			self.newLinkQueue.put(
# 					{
# 						'url'          : link,
# 						'isText'       : True,
# 						'distance'     : distance+1,
# 						'shouldUpsert' : True
# 					}
# 				)

# 		for link in resource:
# 			self.newLinkQueue.put(
# 					{
# 						'url'          : link,
# 						'isText'       : False,
# 						'distance'     : distance+1,
# 						'shouldUpsert' : True
# 					}
# 				)



# 	########################################################################################################################
# 	#
# 	#	########  ########   #######   ######  ########  ######   ######      ######   #######  ##    ## ######## ########   #######  ##
# 	#	##     ## ##     ## ##     ## ##    ## ##       ##    ## ##    ##    ##    ## ##     ## ###   ##    ##    ##     ## ##     ## ##
# 	#	##     ## ##     ## ##     ## ##       ##       ##       ##          ##       ##     ## ####  ##    ##    ##     ## ##     ## ##
# 	#	########  ########  ##     ## ##       ######    ######   ######     ##       ##     ## ## ## ##    ##    ########  ##     ## ##
# 	#	##        ##   ##   ##     ## ##       ##             ##       ##    ##       ##     ## ##  ####    ##    ##   ##   ##     ## ##
# 	#	##        ##    ##  ##     ## ##    ## ##       ##    ## ##    ##    ##    ## ##     ## ##   ###    ##    ##    ##  ##     ## ##
# 	#	##        ##     ##  #######   ######  ########  ######   ######      ######   #######  ##    ##    ##    ##     ##  #######  ########
# 	#
# 	########################################################################################################################

# 	def queueLoop(self):
# 		self.log.info("Fetch thread starting")

# 		# Timeouts is used to track when queues are empty
# 		# Since I have multiple threads, and there are known
# 		# situations where we can be certain that there will be
# 		# only one request (such as at startup), we need to
# 		# have a mechanism for retrying fetches from a queue a few
# 		# times before concluding there is nothing left to do
# 		timeouts = 0
# 		while runStatus.run:
# 			try:
# 				newTodo = self.getToDo(self.FETCH_DISTANCE)
# 				if newTodo:
# 					url, distance = newTodo

# 					self.newLinkQueue.put(
# 							{
# 								'url'          : url,
# 								'isText'       : None,
# 								'distance'     : None,
# 								'shouldUpsert' : False
# 							}
# 						)

# 					try:
# 						self.dispatchUrlRequest(url, distance)
# 					except urllib.error.URLError:
# 						content = "DOWNLOAD FAILED"
# 						content += "<br>"
# 						content += traceback.format_exc()
# 						self.upsert(url, dlstate=-1, contents=content, distance=distance)
# 						self.log.error("`urllib.error.URLError` Exception when downloading.")
# 					except DownloadException:
# 						content = "DOWNLOAD FAILED"
# 						content += "<br>"
# 						content += traceback.format_exc()
# 						self.upsert(url, dlstate=-1, contents=content, distance=distance)
# 						self.log.error("`DownloadException` Exception when downloading.")


# 				else:
# 					timeouts += 1
# 					time.sleep(1)
# 					self.log.info("Fetch task waiting for any potential items to flush to the DB.")

# 				if timeouts > 5:
# 					break

# 			except Exception:
# 				traceback.print_exc()
# 		self.log.info("Fetch thread exiting!")

# 	def crawl(self, shallow=False, checkOnly=False):

# 		self.resetStuckItems()

# 		if hasattr(self, 'preFlight'):
# 			self.preFlight()


# 		# Reset the dlstate on the starting URLs, so thing start up.
# 		haveUrls = set()

# 		if not checkOnly:
# 			if isinstance(self.startUrl, (list, set)):
# 				for url in self.startUrl:
# 					self.log.info("Start URL: '%s'", url)
# 					self.upsert(url, dlstate=0, distance=0, walklimit=-1)
# 			else:
# 				self.upsert(self.startUrl, dlstate=0, distance=0, walklimit=-1)

# 		# with self.transaction():
# 		# 	print('transaction test!')

# 		if shallow:
# 			self.FETCH_DISTANCE = 1


# 		with ThreadPoolExecutor(max_workers=self.threads) as executor:

# 			processes = []
# 			for dummy_x in range(self.threads):
# 				self.log.info("Starting child-thread!")
# 				processes.append(executor.submit(self.queueLoop))


# 			todoIntegrator = time.time()
# 			printInterval = 15  # Print items in queue every 10 seconds
# 			while runStatus.run:

# 				# Every 15 seconds, print how many items remain todo.
# 				if time.time() > (todoIntegrator + printInterval):
# 					self.log.info("Items remaining in todo queue: %s", self.getTodoCount())
# 					todoIntegrator += printInterval

# 				try:
# 					got = self.newLinkQueue.get_nowait()
# 					if not got:
# 						continue
# 					if len(got) == 4:
# 						if not got['url'] in haveUrls:

# 							if got['url'].lower().startswith('http'):
# 								self.log.info("New URL: '%s', distance: %s", got['url'], got['distance'])
# 								# Only reset the downloadstate for content, not
# 								# resources
# 								if got['shouldUpsert']:
# 									if got['isText']:
# 										self.upsert(got['url'], istext=got['isText'], dlstate=0, distance=got['distance'])
# 									else:
# 										self.upsert(got['url'], istext=got['isText'], distance=got['distance'])
# 								haveUrls.add(got['url'])
# 							else:
# 								raise ValueError("Invalid URL added: '%s'", got)
# 					else:
# 						raise ValueError("Data from queue is not a 4-dict? '%s'" % got)

# 				except queue.Empty:
# 					time.sleep(0.01)




# 				if not any([proc.running() for proc in processes]):
# 					self.log.info("All threads stopped. Main thread exiting.")
# 					break
# 			if not runStatus.run:
# 				self.log.warn("Execution stopped because of user-interrupt!")

# 		self.log.info("Crawler scanned a total of '%s' pages", len(haveUrls))
# 		self.log.info("Queue Feeder thread exiting!")


# if __name__ == "__main__":

# 	archiver = SiteArchiver()
# 	print(archiver)


