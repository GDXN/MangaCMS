


import runStatus
runStatus.preloadDicts = False



import logging
import settings
import abc
import threading
import urllib.parse


import logging
import psycopg2
import os
import traceback
import bs4
import time
import queue
from concurrent.futures import ThreadPoolExecutor

import nameTools

from contextlib import contextmanager

QUERY_DEBUG = False

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



class RowExistsException(Exception):
	pass


class TextScraper(object):

	validKwargs = ["rowid",
					"src",
					"dlstate",
					"url",
					"title",
					"series",
					"contents",
					"istext",
					"mimetype",
					"fspath"]


	tableName = "book_items"

	threads = 1

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



	def __init__(self):
		self.log = logging.getLogger(self.loggerPath)
		self.log.info("Tsuki startup")

		# I have to wrap the DB in locks, since two pages may return
		# identical links at the same time.
		# Using transactions could result in collisions, so we lock.
		# Most of the time is spent in processing pages anyways
		self.dbLock = threading.Lock()

		self.loggers = {}
		self.dbConnections = {}

		self.newLinkQueue = queue.Queue()

		self.lastLoggerIndex = 1

		self.log.info("Loading %s Runner BaseClass", self.pluginName)


		self.checkInitPrimaryDb()

	# More hackiness to make sessions intrinsically thread-safe.
	def __getattribute__(self, name):

		threadName = threading.current_thread().name
		if name == "log" and "Thread-" in threadName:
			if threadName not in self.loggers:
				self.loggers[threadName] = logging.getLogger("%s.Thread-%d" % (self.loggerPath, self.lastLoggerIndex))
				self.lastLoggerIndex += 1
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


	def getItem(self, itemUrl):

		content, handle = self.wg.getpage(itemUrl, returnMultiple=True)
		if not content or not handle:
			raise ValueError("Failed to retreive image from page '%s'!" % itemUrl)

		fileN = urllib.parse.unquote(urllib.parse.urlparse(handle.geturl())[2].split("/")[-1])
		fileN = bs4.UnicodeDammit(fileN).unicode_markup
		mType = handle.info()['Content-Type']

		# If there is an encoding in the content-type (or any other info), strip it out.
		# We don't care about the encoding, since WebFunctions will already have handled that,
		# and returned a decoded unicode object.
		if ";" in mType:
			mType = mType.split(";")[0].strip()

		self.log.info("Retreived file of type '%s', name of '%s' with a size of %0.3f K", mType, fileN, len(content)/1000.0)
		return content, fileN, mType


	def convertToReaderUrl(self, inUrl):
		url = urllib.parse.urljoin(self.baseUrl, inUrl)
		url = '/books/render?url=%s' % urllib.parse.quote(url)
		return url



	def extractLinks(self, pageCtnt):
		soup = bs4.BeautifulSoup(pageCtnt)

		for link in soup.find_all("a"):

			# Skip empty anchor tags
			try:
				turl = link["href"]
			except KeyError:
				continue

			url = urllib.parse.urljoin(self.baseUrl, turl)

			# Filter by domain
			if not self.baseUrl in url:
				continue

			# and by blocked words
			hadbad = False
			for badword in self.badwords:
				if badword in url:
					hadbad = True
			if hadbad:
				continue

			# Remove any URL fragments causing multiple retreival of the same resource.
			url = url.split("#")[0]

			# upsert for `url`. Reset dlstate if needed

			self.newLinkQueue.put(url)



		for imtag in soup.find_all("img"):
						# Skip empty anchor tags
			try:
				turl = imtag["src"]
			except KeyError:
				continue

			# Skip tags with `img src=""`.
			# No idea why they're there, but they are
			if not url:
				continue

			url = urllib.parse.urljoin(self.baseUrl, turl)

			# Filter by domain
			if not self.baseUrl in url:
				continue

			# and by blocked words
			hadbad = False
			for badword in self.badwords:
				if badword in url:
					hadbad = True
			if hadbad:
				continue

			url = url.split("#")[0]

			# upsert for `url`. Do not reset dlstate to avoid re-transferring binary files.
			self.upsert(url, istext=False)



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


					self.retreiveItemFromUrl(url)

				else:
					timeouts += 1
					time.sleep(1)

				if timeouts > 5:
					break

			self.log.info("Fetch thread exiting!")
		except Exception:
			traceback.print_exc()

	def crawl(self):

		haveUrls = set()
		self.upsert(self.baseUrl, dlstate=0)

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

		self.log.info("Crawler scanned a total of '%s' pages", len(haveUrls))
		self.log.info("Queue Feeder thread exiting!")

	##############################################################################################################################################
	#                      DB Interfacing
	##############################################################################################################################################


	def upsert(self, pgUrl, commit=True, **kwargs):

		cur = self.conn.cursor()



		with transaction(cur, commit=commit):

			cur.execute("SELECT COUNT(*) FROM {tableName} WHERE url=%s;".format(tableName=self.tableName), (pgUrl, ))
			ret = cur.fetchone()[0]
			if not ret:
				self.insertIntoDb(commit=False, url=pgUrl, **kwargs)
			else:
				if kwargs:
					self.updateDbEntry(url=pgUrl, **kwargs)




	def buildInsertArgs(self, **kwargs):

		# Pre-populate with the table keys.
		keys = ["src"]
		values = ["%s"]
		queryArguments = [self.tableKey]

		for key in kwargs.keys():
			if key not in self.validKwargs:
				raise ValueError("Invalid keyword argument: %s" % key)
			keys.append("{key}".format(key=key))
			values.append("%s")
			queryArguments.append("{s}".format(s=kwargs[key]))

		keysStr = ",".join(keys)
		valuesStr = ",".join(values)

		return keysStr, valuesStr, queryArguments


	# Insert new item into DB.
	# MASSIVELY faster if you set commit=False (it doesn't flush the write to disk), but that can open a transaction which locks the DB.
	# Only pass commit=False if the calling code can gaurantee it'll call commit() itself within a reasonable timeframe.
	# Return value is the primary key of the new row.
	def insertIntoDb(self, commit=True, **kwargs):


		keysStr, valuesStr, queryArguments = self.buildInsertArgs(**kwargs)

		query = '''INSERT INTO {tableName} ({keys}) VALUES ({values})  RETURNING dbid;'''.format(tableName=self.tableName, keys=keysStr, values=valuesStr)

		if QUERY_DEBUG:
			print("Query = ", query)
			print("Args = ", queryArguments)

		with self.conn.cursor() as cur:

			with transaction(cur, commit=commit):
				cur.execute(query, queryArguments)
				ret = cur.fetchone()

		if QUERY_DEBUG:
			print("Query ret = ", ret)

		return ret[0]



	# Update entry with key sourceUrl with values **kwargs
	# kwarg names are checked for validity, and to prevent possiblity of sql injection.
	def updateDbEntry(self, dbid=None, url=None, commit=True, **kwargs):

		if not dbid and not url:
			raise ValueError("You need to pass a uniquely identifying value to update a row.")
		if dbid and url:
			raise ValueError("Updating with dbid and url is not currently supported.")

		if dbid:
			setkey = 'dbid'
			rowkey = dbid
		if url:
			setkey = 'url'
			rowkey = url

		queries = []
		qArgs = []
		for key in kwargs.keys():
			if key not in self.validKwargs:
				raise ValueError("Invalid keyword argument: %s" % key)
			else:
				queries.append("{k}=%s".format(k=key))
				qArgs.append(kwargs[key])

		qArgs.append(rowkey)
		qArgs.append(self.tableKey)
		column = ", ".join(queries)


		query = '''UPDATE {tableName} SET {v} WHERE {setkey}=%s AND src=%s;'''.format(tableName=self.tableName, setkey=setkey, v=column)

		if QUERY_DEBUG:
			print("Query = ", query)
			print("Args = ", qArgs)

		with self.conn.cursor() as cur:
			with transaction(cur, commit=commit):
				cur.execute(query, qArgs)



	def saveFile(self, url, mimetype, fileName, content):



		with self.conn.cursor() as cur:
			with transaction(cur):

				cur.execute("SELECT dbid, fspath, contents, mimetype  FROM {tableName} WHERE url=%s;".format(tableName=self.tableName), (url, ))
				dbid, havePath, haveCtnt, haveMime = cur.fetchone()
				# self.log.info('havePath, haveCtnt, haveMime - %s, %s, %s', havePath, haveCtnt, haveMime)


				fqPath = self.getFilenameFromIdName(dbid, fileName)

				newRowDict = {  "dlstate" : 2,
								"series"  : None,
								"contents": len(content),
								"istext"  : False,
								"mimetype": mimetype,
								"fspath"  : fqPath}


				self.updateDbEntry(url=url, commit=False, **newRowDict)



		with open(fqPath, "wb") as fp:
			fp.write(content)




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


	def checkInitPrimaryDb(self):
		with self.conn.cursor() as cur:

			cur.execute('''CREATE TABLE IF NOT EXISTS {tableName} (
												dbid      SERIAL PRIMARY KEY,
												src       TEXT NOT NULL,
												dlstate   INTEGER DEFAULT 0,
												url       text UNIQUE NOT NULL,

												title     text,
												series    text,
												contents  text,
												istext    boolean DEFAULT TRUE,
												mimetype  text,
												fspath    text DEFAULT '');'''.format(tableName=self.tableName))


			cur.execute("SELECT relname FROM pg_class;")
			haveIndexes = cur.fetchall()
			haveIndexes = [index[0] for index in haveIndexes]



			indexes = [
				("%s_source_index"     % self.tableName, self.tableName, '''CREATE INDEX %s ON %s (src     );'''  ),
				("%s_istext_index"     % self.tableName, self.tableName, '''CREATE INDEX %s ON %s (istext  );'''  ),
				("%s_dlstate_index"    % self.tableName, self.tableName, '''CREATE INDEX %s ON %s (dlstate );'''  ),
				("%s_url_index"        % self.tableName, self.tableName, '''CREATE INDEX %s ON %s (url     );'''  ),
				("%s_title_index"      % self.tableName, self.tableName, '''CREATE INDEX %s ON %s (title   );'''  )
			]


			for name, table, nameFormat in indexes:
				if not name.lower() in haveIndexes:
					cur.execute(nameFormat % (name, table))



		self.conn.commit()

		self.log.info("Retreived page database created")


