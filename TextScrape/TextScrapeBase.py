


import runStatus
runStatus.preloadDicts = False

# import Levenshtein as lv

import markdown
import logging
import settings
import abc
import threading
import urllib.parse
import functools
import operator as opclass

import sql
# import sql.operators as sqlo


import hashlib
import psycopg2
import os
import traceback
import bs4
import readability.readability
import time
import queue
from concurrent.futures import ThreadPoolExecutor

import nameTools

from contextlib import contextmanager

class DownloadException(Exception):
	pass

@contextmanager
def transaction(cursor, commit=True):
	if commit:
		cursor.execute("BEGIN;")

	try:
		yield

	except Exception as e:
		if commit:
			cursor.execute("ROLLBACK;")
		raise e

	finally:
		if commit:
			cursor.execute("COMMIT;")




def rebaseUrl(url, base):
	"""Rebase one url according to base"""

	parsed = urllib.parse.urlparse(url)
	if parsed.scheme == parsed.netloc == '':
		return urllib.parse.urljoin(base, url)
	else:
		return url


# All tags you need to look into to do link canonization
# source: http://stackoverflow.com/q/2725156/414272
# TODO: "These aren't necessarily simple URLs ..."
urlContainingTargets = [
	('a', 'href'), ('applet', 'codebase'), ('area', 'href'), ('base', 'href'),
	('blockquote', 'cite'), ('body', 'background'), ('del', 'cite'),
	('form', 'action'), ('frame', 'longdesc'), ('frame', 'src'),
	('head', 'profile'), ('iframe', 'longdesc'), ('iframe', 'src'),
	('img', 'longdesc'), ('img', 'src'), ('img', 'usemap'), ('input', 'src'),
	('input', 'usemap'), ('ins', 'cite'), ('link', 'href'),
	('object', 'classid'), ('object', 'codebase'), ('object', 'data'),
	('object', 'usemap'), ('q', 'cite'), ('script', 'src'), ('audio', 'src'),
	('button', 'formaction'), ('command', 'icon'), ('embed', 'src'),
	('html', 'manifest'), ('input', 'formaction'), ('source', 'src'),
	('video', 'poster'), ('video', 'src'),
]


class RowExistsException(Exception):
	pass


class TextScraper(metaclass=abc.ABCMeta):

	# Abstract class (must be subclassed)
	__metaclass__ = abc.ABCMeta

	validKwargs = []

	tableName       = "book_items"
	changeTableName = "book_changes"

	threads = 2

	QUERY_DEBUG = False

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


	decompose       = []

	# General annoying comment bullshit and sharing widgets.
	#
	decomposeBefore = [
		{'name'     : 'likes-master'},  # Bullshit sharing widgets
		{'id'       : 'jp-post-flair'},
		{'class'    : 'commentlist'},  # Scrub out the comments so we don't try to fetch links from them
		{'class'    : 'post-share-buttons'},
		{'class'    : 'comments'},
		{'id'       : 'comments'},
	]
	allImages = False


	fileDomains = set()

	_scannedDomains = set()
	scannedDomains = set()

	stripTitle = ''

	def __init__(self):
		# These two lines HAVE to be before ANY logging statements, or the automagic thread
		# logging context management will fail.
		self.loggers = {}
		self.lastLoggerIndex = 1
		self.scannedDomains.add(self.baseUrl)

		# Lower case all the domains, since they're not case sensitive, and it case mismatches can break matching.
		# We also extract /just/ the netloc, so http/https differences don't cause a problem.
		self._scannedDomains = set()
		for url in self.scannedDomains:
			url = urllib.parse.urlsplit(url.lower()).netloc
			if not url:
				raise ValueError("One of the scanned domains collapsed down to an empty string: '%s'!" % url)
			self._scannedDomains.add(url)

		# Loggers are set up dynamically on first-access.
		self.log.info("TextScrape Base startup")

		# I have to wrap the DB in locks, since two pages may return
		# identical links at the same time.
		# Using transactions could result in collisions, so we lock.
		# Most of the time is spent in processing pages anyways
		self.dbLock = threading.Lock()

		self.dbConnections = {}

		self.newLinkQueue = queue.Queue()


		self.log.info("Loading %s Runner BaseClass", self.pluginName)


		self.checkInitPrimaryDb()

		self.fileDomains.add(urllib.parse.urlsplit(self.baseUrl.lower()).netloc)


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


		elif name == "conn":
			if threadName not in self.dbConnections:

				# First try local socket connection, fall back to a IP-based connection.
				# That way, if the server is local, we get the better performance of a local socket.
				try:
					self.dbConnections[threadName] = psycopg2.connect(dbname=settings.DATABASE_DB_NAME, user=settings.DATABASE_USER,password=settings.DATABASE_PASS)
				except psycopg2.OperationalError:
					self.dbConnections[threadName] = psycopg2.connect(host=settings.DATABASE_IP, dbname=settings.DATABASE_DB_NAME, user=settings.DATABASE_USER,password=settings.DATABASE_PASS)

				# self.dbConnections[threadName].autocommit = True
			return self.dbConnections[threadName]



		else:
			return object.__getattribute__(self, name)




	# ------------------------------------------------------------------------------------------------------------------
	#                      Web Scraping stuff
	# ------------------------------------------------------------------------------------------------------------------



	def urlClean(self, url):

		while True:
			url2 = urllib.parse.unquote(url)
			url2 = url2.split("#")[0]
			url2 = url2.split("?")[0]
			if url2 == url:
				break
			url = url2

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
		inUrl = self.preprocessReaderUrl(inUrl)
		url = urllib.parse.urljoin(self.baseUrl, inUrl)
		url = '/books/render?url=%s' % urllib.parse.quote(url)
		return url

	# check if domain `url` is a sub-domain of the scanned domains.
	def checkDomain(self, url):
		# print(self.scannedDomains)
		# print("CheckDomain", any([rootUrl in url.lower() for rootUrl in self.scannedDomains]), url)
		return any([rootUrl in url.lower() for rootUrl in self._scannedDomains])

	def extractLinks(self, soup):
		# All links have been resolved to fully-qualified paths at this point.

		for link in soup.find_all("a"):

			# Skip empty anchor tags
			try:
				url = link["href"]
			except KeyError:
				continue

			# Filter by domain
			# print("Filtering", self.checkDomain(url), url)
			if not self.checkDomain(url):
				continue

			# and by blocked words
			hadbad = False
			for badword in self.badwords:
				if badword in url:
					hadbad = True
			if hadbad:
				continue

			# Remove any URL fragments causing multiple retreival of the same resource.
			url = self.urlClean(url)

			# upsert for `url`. Reset dlstate if needed

			self.newLinkQueue.put(url)



		for imtag in soup.find_all("img"):
						# Skip empty anchor tags
			try:
				url = imtag["src"]
			except KeyError:
				continue

			# Skip tags with `img src=""`.
			# No idea why they're there, but they are
			if not url:
				continue

			# Filter by domain
			if not self.allImages and not any([base in url for base in self.fileDomains]):
				continue

			# and by blocked words
			hadbad = False
			for badword in self.badwords:
				if badword in url:
					hadbad = True
			if hadbad:
				continue


			# upsert for `url`. Do not reset dlstate to avoid re-transferring binary files.
			url = self.urlClean(url)
			self.upsert(url, istext=False)


	def convertToReaderImage(self, inStr):
		inStr = self.urlClean(inStr)
		return self.convertToReaderUrl(inStr)

	def relink(self, soup):

		for aTag in soup.find_all("a"):
			try:
				if self.checkDomain(aTag["href"]):
					aTag["href"] = self.convertToReaderUrl(aTag["href"])
			except KeyError:
				continue

		for imtag in soup.find_all("img"):
			try:
				imtag["src"] = self.convertToReaderImage(imtag["src"])
				# print("New image URL", imtag['src'])

				# Force images that are oversize to fit the window.
				imtag["style"] = 'max-width: 95%;'

			except KeyError:
				continue

		return soup



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



	def canonizeUrls(self, soup, pageUrl):
		self.log.info("Making all links on page absolute.")

		for (tag, attr) in urlContainingTargets:
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
				instance.decompose() # This call permutes the tree!
		return soup

	def cleanHtmlPage(self, soup, url=None):

		# since readability strips tag attributes, we preparse with BS4,
		# parse with readability, and then do reformatting *again* with BS4
		# Yes, this is ridiculous.

		ctnt = soup.prettify()
		doc = readability.readability.Document(ctnt)
		doc.parse()
		content = doc.content()

		soup = bs4.BeautifulSoup(content)
		soup = self.relink(soup)
		contents = ''


		# Generate HTML string for /just/ the contents of the <body> tag.
		for item in soup.body.contents:
			if type(item) is bs4.Tag:
				contents += item.prettify()
			elif type(item) is bs4.NavigableString:
				contents += item
			else:
				print("Wat", item)


		title = doc.title()
		title = title.replace(self.stripTitle, "")
		title = title.strip()

		return title, contents



	# Process a plain HTML page.
	# This call does a set of operations to permute and clean a HTML page.
	#
	# First, it decomposes all tags with attributes dictated in the `decomposeBefore` class variable
	# it then canonizes all the URLs on the page, extracts all the URLs from the page,
	# then decomposes all the tags in the `decompose` class variable, feeds the content through
	# readability, and finally saves the processed HTML into the database
	def processHtmlPage(self, url, content, mimeType):
		self.log.info("Processing '%s' as HTML.", url)


		soup = bs4.BeautifulSoup(content)

		soup = self.decomposeItems(soup, self.decomposeBefore)
		soup = self.canonizeUrls(soup, url)

		if self.checkDomain(url):
			self.extractLinks(soup)

		soup = self.decomposeItems(soup, self.decompose)

		pgTitle, pgBody = self.cleanHtmlPage(soup)
		self.log.info("Page with title '%s' retreived.", pgTitle)
		self.updateDbEntry(url=url, title=pgTitle, contents=pgBody, mimetype=mimeType, dlstate=2)


	# Format a text-file using markdown to make it actually nice to look at.
	def processAsMarkdown(self, content, url):
		self.log.info("Plain-text file. Processing with markdown.")
		# Take the first non-empty line, and just assume it's the title. It'll be close enough.
		title = content.strip().split("\n")[0].strip()
		content = markdown.markdown(content)

		self.updateDbEntry(url=url, title=title, contents=content, mimetype='text/html', dlstate=2)


	# This is the main function that's called by the task management system.
	# Retreive remote content at `url`, call the appropriate handler for the
	# transferred content (e.g. is it an image/html page/binary file)
	def retreiveItemFromUrl(self, url):

		url = self.urlClean(url)
		# Snip off leading slashes that have shown up a few times.
		if url.startswith("//"):
			url = 'http://'+url[2:]

		self.log.info("Fetching page '%s'", url)
		try:
			content, fName, mimeType = self.getItem(url)
		except ValueError:

			for line in traceback.format_exc().split("\n"):
				self.log.critical(line)
			self.upsert(url, dlstate=-1, contents='Error downloading!')
			return

		if mimeType == 'text/html':
			self.processHtmlPage(url, content, mimeType)

		elif mimeType in ['text/plain']:
			self.processAsMarkdown(content, url)
		elif mimeType in ['text/xml', 'text/atom+xml']:
			self.log.info("XML File?")
			self.log.info("URL: '%s'", url)

		elif mimeType in ["image/gif", "image/jpeg", "image/pjpeg", "image/png", "image/svg+xml", "image/vnd.djvu"]:
			self.log.info("Processing '%s' as an image file.", url)
			self.saveFile(url, mimeType, fName, content)

		elif mimeType in ["application/octet-stream", "application/x-mobipocket-ebook", "application/pdf"]:
			self.log.info("Processing '%s' as an binary file.", url)
			self.saveFile(url, mimeType, fName, content)

		else:
			self.log.warn("Unknown MIME Type? '%s', Url: '%s'", mimeType, url)



	########################################################################################################################
	#                      Process management
	########################################################################################################################

	def queueLoop(self):
		self.log.info("Fetch thread starting")
		try:
			# Timeouts is used to track when queues are empty
			# Since I have multiple threads, and there are known
			# situations where we can be certain that there will be
			# only one request (such as at startup), we need to
			# have a mechanism for retrying fetches from a queue a few
			# times before concluding there is nothing left to do
			timeouts = 0
			while runStatus.run:

				url = self.getToDo()
				if url:

					try:
						self.retreiveItemFromUrl(url)
					except urllib.error.URLError:
						content = "DOWNLOAD FAILED"
						content += "<br>"
						content += traceback.format_exc()
						self.upsert(url, dlstate=-1, contents=content)
					except DownloadException:
						content = "DOWNLOAD FAILED"
						content += "<br>"
						content += traceback.format_exc()
						self.upsert(url, dlstate=-1, contents=content)


				else:
					timeouts += 1
					time.sleep(1)

				if timeouts > 5:
					break

			self.log.info("Fetch thread exiting!")
		except Exception:
			traceback.print_exc()

	def crawl(self):

		self.resetStuckItems()

		haveUrls = set()
		if isinstance(self.startUrl, list):
			for url in self.startUrl:
				self.upsert(url, dlstate=0)
		else:
			self.upsert(self.startUrl, dlstate=0)

		with ThreadPoolExecutor(max_workers=self.threads) as executor:

			processes = []
			for dummy_x in range(self.threads):
				self.log.info("Starting child-thread!")
				processes.append(executor.submit(self.queueLoop))


			while runStatus.run:
				try:
					got = self.newLinkQueue.get_nowait()
					if not got in haveUrls:
						self.upsert(got, dlstate=0)
						haveUrls.add(got)

				except queue.Empty:
					time.sleep(0.01)




				if not any([proc.running() for proc in processes]):
					self.log.info("All threads stopped. Main thread exiting.")
					break
			if not runStatus.run:
				self.log.warn("Execution stopped because of user-interrupt!")

		self.log.info("Crawler scanned a total of '%s' pages", len(haveUrls))
		self.log.info("Queue Feeder thread exiting!")



	##############################################################################################################################################
	#                      Schema definition
	##############################################################################################################################################

	def checkInitPrimaryDb(self):
		with self.conn.cursor() as cur:

			cur.execute('''CREATE TABLE IF NOT EXISTS {tableName} (
												dbid      SERIAL PRIMARY KEY,
												src       TEXT NOT NULL,
												dlstate   INTEGER DEFAULT 0,
												url       CITEXT UNIQUE NOT NULL,

												title     text,
												series    CITEXT,
												contents  text,
												istext    boolean DEFAULT TRUE,
												fhash     CITEXT,
												mimetype  CITEXT,
												fspath    text DEFAULT '',
												UNIQUE(fhash));'''.format(tableName=self.tableName))



			cur.execute('''CREATE TABLE IF NOT EXISTS {tableName} (
												dbid       SERIAL PRIMARY KEY,
												src        TEXT NOT NULL,
												url        CITEXT NOT NULL,
												change     real NOT NULL,
												title      text,
												changeDate double precision NOT NULL
												);'''.format(tableName=self.changeTableName))


			cur.execute("SELECT relname FROM pg_class;")
			haveIndexes = cur.fetchall()
			haveIndexes = [index[0] for index in haveIndexes]

			indexes = [
				("%s_source_index"     % self.tableName, self.tableName, '''CREATE INDEX %s ON %s (src     );'''  ),
				("%s_istext_index"     % self.tableName, self.tableName, '''CREATE INDEX %s ON %s (istext  );'''  ),
				("%s_dlstate_index"    % self.tableName, self.tableName, '''CREATE INDEX %s ON %s (dlstate );'''  ),
				("%s_url_index"        % self.tableName, self.tableName, '''CREATE INDEX %s ON %s (url     );'''  ),
				("%s_title_index"      % self.tableName, self.tableName, '''CREATE INDEX %s ON %s (title   );'''  ),
				("%s_fhash_index"      % self.tableName, self.tableName, '''CREATE INDEX %s ON %s (fhash   );'''  ),
				("%s_title_coll_index" % self.tableName, self.tableName, '''CREATE INDEX %s ON %s USING BTREE (title COLLATE "en_US" text_pattern_ops);'''  ),


				("%s_date_index"       % self.changeTableName, self.changeTableName, '''CREATE INDEX %s ON %s (changeDate);''' ),
				("%s_src_index"        % self.changeTableName, self.changeTableName, '''CREATE INDEX %s ON %s (src   );'''     ),
				("%s_url_index"        % self.changeTableName, self.changeTableName, '''CREATE INDEX %s ON %s (url   );'''     ),
				("%s_change_index"     % self.changeTableName, self.changeTableName, '''CREATE INDEX %s ON %s (change   );'''  ),
			]

		# CREATE INDEX book_title_trigram ON book_items USING gin (title gin_trgm_ops);

		# CREATE INDEX  book_items_title_coll_index ON book_items USING BTREE (title COLLATE "en_US" text_pattern_ops);
		# CREATE INDEX  book_items_fhash_index ON book_items (fhash);

		# CREATE INDEX title_collate_index ON book_items USING BTREE (title COLLATE "en_US" text_pattern_ops);
		# EXPLAIN ANALYZE SELECT COUNT(*) FROM book_items WHERE title LIKE 's%';


			for name, table, nameFormat in indexes:
				if not name.lower() in haveIndexes:
					cur.execute(nameFormat % (name, table))

		self.conn.commit()
		self.log.info("Retreived page database created")

		self.validKwargs = ['dbid', 'src', 'dlstate', 'url', 'title', 'series', 'contents', 'istext', 'fhash', 'mimetype', 'fspath']


		self.table = sql.Table(self.tableName.lower())

		self.cols = (
				self.table.dbid,
				self.table.src,
				self.table.dlstate,
				self.table.url,
				self.table.title,
				self.table.series,
				self.table.contents,
				self.table.istext,
				self.table.fhash,
				self.table.mimetype,
				self.table.fspath
			)


		self.colMap = {
				"dbid"       : self.table.dbid,
				"src"        : self.table.src,
				"dlstate"    : self.table.dlstate,
				"url"        : self.table.url,
				"title"      : self.table.title,
				"series"     : self.table.series,
				"contents"   : self.table.contents,
				"istext"     : self.table.istext,
				"fhash"      : self.table.fhash,
				"mimetype"   : self.table.mimetype,
				"fspath"     : self.table.fspath
			}


	##############################################################################################################################################
	#                      DB Interfacing
	##############################################################################################################################################


	def keyToCol(self, key):
		key = key.lower()
		if not key in self.colMap:
			raise ValueError("Invalid column name '%s'" % key)
		return self.colMap[key]


	def sqlBuildConditional(self, **kwargs):
		operators = []

		# Short circuit and return none (so the resulting where clause is all items) if no kwargs are passed.
		if not kwargs:
			return None

		for key, val in kwargs.items():
			operators.append((self.keyToCol(key) == val))

		# This is ugly as hell, but it functionally returns x & y & z ... for an array of [x, y, z]
		# And allows variable length arrays.
		conditional = functools.reduce(opclass.and_, operators)
		return conditional


	def sqlBuildInsertArgs(self, returning=None, **kwargs):

		cols = [self.table.src]
		vals = [self.tableKey]

		for key, val in kwargs.items():
			key = key.lower()

			if key not in self.colMap:
				raise ValueError("Invalid column name for insert! '%s'" % key)
			cols.append(self.colMap[key])
			vals.append(val)

		query = self.table.insert(columns=cols, values=[vals], returning=returning)

		query, params = tuple(query)

		return query, params


	# Insert new item into DB.
	# MASSIVELY faster if you set commit=False (it doesn't flush the write to disk), but that can open a transaction which locks the DB.
	# Only pass commit=False if the calling code can gaurantee it'll call commit() itself within a reasonable timeframe.
	def insertIntoDb(self, commit=True, **kwargs):
		query, queryArguments = self.sqlBuildInsertArgs(returning=[self.table.dbid], **kwargs)

		if self.QUERY_DEBUG:
			print("Query = ", query)
			print("Args = ", queryArguments)

		with self.conn.cursor() as cur:
			with transaction(cur, commit=commit):
				cur.execute(query, queryArguments)
				ret = cur.fetchone()

		if self.QUERY_DEBUG:
			print("Query ret = ", ret)

		return ret[0]


	def generateUpdateQuery(self, **kwargs):
		if "dbid" in kwargs:
			where = (self.table.dbid == kwargs.pop('dbid'))
		elif "url" in kwargs:
			where = (self.table.url == kwargs.pop('url'))
		else:
			raise ValueError("GenerateUpdateQuery must be passed a single unique column identifier (either dbId or url)")

		cols = []
		vals = []

		for key, val in kwargs.items():
			key = key.lower()

			if key not in self.colMap:
				raise ValueError("Invalid column name for insert! '%s'" % key)
			cols.append(self.colMap[key])
			vals.append(val)

		query = self.table.update(columns=cols, values=vals, where=where)
		query, params = tuple(query)

		return query, params



	# Update entry with key sourceUrl with values **kwargs
	# kwarg names are checked for validity, and to prevent possiblity of sql injection.
	def updateDbEntry(self, commit=True, **kwargs):

		self.insertDelta(**kwargs)

		query, queryArguments = self.generateUpdateQuery(**kwargs)

		if self.QUERY_DEBUG:
			print("Query = ", query)
			print("Args = ", queryArguments)

		with self.conn.cursor() as cur:
			with transaction(cur, commit=commit):
				cur.execute(query, queryArguments)



	def deleteDbEntry(self, commit=True, **kwargs):
		if len(kwargs) != 1:
			raise ValueError("deleteDbEntry only supports calling with a single kwarg", kwargs)

		validCols = ["dbid", "url"]


		key, val = kwargs.popitem()
		if key not in validCols:
			raise ValueError("Invalid column key for delete query: %s. Must be either 'dbid' or 'url'" % key)

		where = (self.colMap[key.lower()] == val)

		query = self.table.delete(where=where)

		query, args = tuple(query)


		if self.QUERY_DEBUG:
			print("Query = ", query)
			print("Args = ", args)

		with self.conn.cursor() as cur:
			with transaction(cur, commit=commit):
				cur.execute(query, args)





	def getRowsByValue(self, limitByKey=True, **kwargs):
		if limitByKey and self.tableKey:
			kwargs["src"] = self.tableKey


		where = self.sqlBuildConditional(**kwargs)

		wantCols = (
				self.table.dbid,
				self.table.src,
				self.table.dlstate,
				self.table.url,
				self.table.title,
				self.table.series,
				self.table.contents,
				self.table.istext,
				self.table.fhash,
				self.table.mimetype,
				self.table.fspath
			)

		query = self.table.select(*wantCols, order_by=sql.Desc(self.table.dbid), where=where)

		query, quargs = tuple(query)

		if self.QUERY_DEBUG:
			print("Query = ", query)
			print("args = ", quargs)

		with self.conn.cursor() as cur:

			#wrap queryies in transactions so we don't have hanging db handles.
			with transaction(cur):
				cur.execute(query, quargs)
				rets = cur.fetchall()



		retL = []
		for row in rets:

			keys = ['dbid', 'src', 'dlstate', 'url', 'title', 'series', 'contents', 'istext', 'fhash', 'mimetype', 'fspath']
			retL.append(dict(zip(keys, row)))
		return retL

	def getRowByValue(self, **kwargs):
		rows = self.getRowsByValue(**kwargs)
		if len(rows) == 1:
			return rows.pop()
		if len(rows) == 0:
			return None
		else:
			raise ValueError("Got multiple rows for selection. Wat?")




	def saveFile(self, url, mimetype, fileName, content):


		hadFile = False
		# Yeah, I'm hashing twice in lots of cases. Bite me
		fHash = self.getHash(content)

		with self.conn.cursor() as cur:

			# Look for existing files with the same MD5sum. If there are any, just point the new file at the
			# fsPath of the existing one, rather then creating a new file on-disk.
			with transaction(cur):
				cur.execute("SELECT fspath  FROM {tableName} WHERE fhash=%s;".format(tableName=self.tableName), (fHash, ))
				row = cur.fetchone()
				if row:
					self.log.info("Already downloaded file. Not creating duplicates.")
					hadFile = True
					fqPath = row[0]

			with transaction(cur):

				cur.execute("SELECT dbid, fspath, contents, mimetype  FROM {tableName} WHERE url=%s;".format(tableName=self.tableName), (url, ))
				row = cur.fetchone()
				if not row:
					self.log.critical("Failure when saving file for URL '%s'", url)
					self.log.critical("File name: '%s'", fileName)
					return

				dbid, havePath, haveCtnt, haveMime = row
				# self.log.info('havePath, haveCtnt, haveMime - %s, %s, %s', havePath, haveCtnt, haveMime)

				if not hadFile:
					fqPath = self.getFilenameFromIdName(dbid, fileName)

				newRowDict = {  "dlstate" : 2,
								"series"  : None,
								"contents": len(content),
								"istext"  : False,
								"mimetype": mimetype,
								"fspath"  : fqPath,
								"fhash"   : fHash}


				self.updateDbEntry(url=url, commit=False, **newRowDict)


		if not hadFile:
			try:
				with open(fqPath, "wb") as fp:
					fp.write(content)
			except OSError:
				self.log.error("Error when attempting to save file. ")
				with transaction(cur):
					newRowDict = {"dlstate" : -1}
					self.updateDbEntry(url=url, commit=False, **newRowDict)


	def getToDo(self):
		cur = self.conn.cursor()

		# Retreiving todo items must be atomic, so we lock for that.
		with self.dbLock:
			with transaction(cur):

				cur.execute('''SELECT dbid, url FROM {tableName} WHERE dlstate=%s AND src=%s ORDER BY istext ASC LIMIT 1;'''.format(tableName=self.tableName), (0, self.tableKey))
				row = cur.fetchone()




				if not row:
					return False
				else:
					dbid, url = row
					cur.execute('UPDATE {tableName} SET dlstate=%s WHERE dbid=%s;'.format(tableName=self.tableName), (1, dbid))
					return url



	def resetStuckItems(self):
		self.log.info("Resetting stuck downloads in DB")
		with self.conn.cursor() as cur:
			cur.execute('''UPDATE {tableName} SET dlState=0 WHERE dlState=1 AND src=%s'''.format(tableName=self.tableName), (self.tableKey, ))
		self.conn.commit()
		self.log.info("Download reset complete")

	# Override to filter items that get
	def changeFilter(self, url, title, changePercentage):
		return False

	def insertChangeStats(self, url, changePercentage, title):

		# Skip title cruft on baka-tsuki
		if self.changeFilter(url, title, changePercentage):
			return

		with self.conn.cursor() as cur:
			query = '''INSERT INTO {changeTable} (src, url, change, title, changeDate) VALUES (%s, %s, %s, %s, %s)'''.format(changeTable=self.changeTableName)
			values = (self.tableKey, url, changePercentage, title, time.time())
			cur.execute(query, values)


	##############################################################################################################################################
	# Higher level DB Interfacing
	##############################################################################################################################################


	def upsert(self, pgUrl, commit=True, **kwargs):

		cur = self.conn.cursor()


		try:
			with transaction(cur, commit=commit):
				self.insertIntoDb(commit=False, url=pgUrl, **kwargs)
				return
		except psycopg2.IntegrityError:
			if kwargs:
				with transaction(cur, commit=commit):
					self.updateDbEntry(url=pgUrl, **kwargs)


	def insertDelta(self, **kwargs):

		if 'istext' in kwargs and not kwargs['istext']:
			return

		if not 'contents' in kwargs:
			return

		if 'url' in kwargs:
			old = self.getRowByValue(url=kwargs['url'])
		elif 'dbid' in kwargs:
			old = self.getRowByValue(dbid=kwargs['dbid'])
		else:
			raise ValueError("No identifying info in insertDelta call!")

		if 'title' in kwargs:
			title = kwargs['title']
		else:
			title = old['title']

		if not title:
			title = ''

		if not old:
			self.log.error("Couldn't find original db entry for item?")
			return

		if old['contents'] == None:
			old['contents'] = ''

		oldStr = str(old['contents'])
		newStr = str(kwargs['contents'])

		# self.log.info("Calculating edit-distance")
		self.log.info("Calculating Coarse length change")
		print("String lengths", len(oldStr), len(newStr))

		lChange = abs(len(oldStr) - len(newStr))
		lTotal = max((len(oldStr), len(newStr)))
		# distance = lv.distance(oldStr, newStr)
		# distance = 0
		# self.log.info("Done")
		# space = min((len(oldStr), len(newStr)))

		if lTotal == 0:
			lTotal = 1

		change = (lChange / lTotal) * 100
		change = min((change, 100))
		self.log.info("Percent change in page contents: %s", change)

		self.insertChangeStats(old['url'], change, title)


	def getHash(self, fCont):

		m = hashlib.md5()
		m.update(fCont)
		return m.hexdigest()
