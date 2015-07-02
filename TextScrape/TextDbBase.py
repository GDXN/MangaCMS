

#pylint: disable=W0201, W0142

import runStatus
runStatus.preloadDicts = False

# import Levenshtein as lv


import sql.conditionals as sqlc
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
import os.path
import time
import nameTools
import DbBase


class RowExistsException(Exception):
	pass

# This whole mess is getting too hueg and clumsy. FIXME!


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


class TextDbBase(DbBase.DbBase, metaclass=abc.ABCMeta):

	# Abstract class (must be subclassed)
	__metaclass__ = abc.ABCMeta

	@abc.abstractproperty
	def tableName(self):
		pass

	@abc.abstractproperty
	def changeTableName(self):
		pass

	@abc.abstractproperty
	def tableKey(self):
		pass

	QUERY_DEBUG = False

	def __init__(self):
		# These two lines HAVE to be before ANY logging statements, or the automagic thread
		# logging context management will fail.
		self.loggers = {}
		self.lastLoggerIndex = 1

		super().__init__()

		# I have to wrap the DB in locks, since two pages may return
		# identical links at the same time.
		# Using transactions could result in collisions, so we lock.
		# Most of the time is spent in processing pages anyways
		self.dbLock = threading.Lock()

		self.checkInitPrimaryDb()



	# More hackiness to make sessions intrinsically thread-safe.
	@property
	def log(self):

		threadName = threading.current_thread().name
		if "Thread-" in threadName:
			if threadName not in self.loggers:
				self.loggers[threadName] = logging.getLogger("%s.Thread-%d" % (self.loggerPath, self.lastLoggerIndex))
				self.lastLoggerIndex += 1

		# If we're not called in the context of a thread, just return the base log-path
		else:
			self.loggers[threadName] = logging.getLogger("%s" % (self.loggerPath,))


		return self.loggers[threadName]



	##############################################################################################################################################
	#
	#
	#	 ######   ######  ##     ## ######## ##     ##    ###       ########  ######## ######## #### ##    ## #### ######## ####  #######  ##    ##
	#	##    ## ##    ## ##     ## ##       ###   ###   ## ##      ##     ## ##       ##        ##  ###   ##  ##     ##     ##  ##     ## ###   ##
	#	##       ##       ##     ## ##       #### ####  ##   ##     ##     ## ##       ##        ##  ####  ##  ##     ##     ##  ##     ## ####  ##
	#	 ######  ##       ######### ######   ## ### ## ##     ##    ##     ## ######   ######    ##  ## ## ##  ##     ##     ##  ##     ## ## ## ##
	#	      ## ##       ##     ## ##       ##     ## #########    ##     ## ##       ##        ##  ##  ####  ##     ##     ##  ##     ## ##  ####
	#	##    ## ##    ## ##     ## ##       ##     ## ##     ##    ##     ## ##       ##        ##  ##   ###  ##     ##     ##  ##     ## ##   ###
	#	 ######   ######  ##     ## ######## ##     ## ##     ##    ########  ######## ##       #### ##    ## ####    ##    ####  #######  ##    ##
	#
	#
	##############################################################################################################################################

	def checkInitPrimaryDb(self):
		with self.transaction() as cur:

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
												distance  INTEGER DEFAULT 2147483648,
												walklimit INTEGER DEFAULT -1,
												netloc    CITEXT
												);'''.format(tableName=self.tableName))


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
				("%s_netloc_index"     % self.changeTableName, self.changeTableName, '''CREATE INDEX %s ON %s (change   );'''  ),
				("%s_title_trigram"    % self.changeTableName, self.changeTableName, '''CREATE INDEX %s ON %s USING gin (title gin_trgm_ops);'''  ),
			]

		# CREATE INDEX book_series_name_trigram ON book_series USING gin (itemname gin_trgm_ops);
		# CREATE INDEX book_title_trigram ON book_items USING gin (title gin_trgm_ops);

		# ALTER INDEX book_title_trigram RENAME TO book_items_title_trigram;

		# CREATE INDEX  book_items_title_coll_index ON book_items USING BTREE (title COLLATE "en_US" text_pattern_ops);
		# CREATE INDEX  book_items_fhash_index ON book_items (fhash);

		# CREATE INDEX title_collate_index ON book_items USING BTREE (title COLLATE "en_US" text_pattern_ops);
		# EXPLAIN ANALYZE SELECT COUNT(*) FROM book_items WHERE title LIKE 's%';


			for name, table, nameFormat in indexes:
				if not name.lower() in haveIndexes:
					cur.execute(nameFormat % (name, table))


		self.log.info("Retreived page database created")



		self.validKwargs = [
						'dbid',
						'src',
						'dlstate',
						'url',
						'title',
						'netloc',
						'series',
						'contents',
						'istext',
						'fhash',
						'mimetype',
						'fspath',
						'distance',
						'walklimit'
					]


		self.table = sql.Table(self.tableName.lower())

		self.cols = (
				self.table.dbid,
				self.table.src,
				self.table.dlstate,
				self.table.url,
				self.table.title,
				self.table.netloc,
				self.table.series,
				self.table.contents,
				self.table.istext,
				self.table.fhash,
				self.table.mimetype,
				self.table.fspath,
				self.table.distance,
				self.table.walklimit,
			)


		self.colMap = {
				"dbid"       : self.table.dbid,
				"src"        : self.table.src,
				"dlstate"    : self.table.dlstate,
				"url"        : self.table.url,
				"netloc"     : self.table.netloc,
				"title"      : self.table.title,
				"series"     : self.table.series,
				"contents"   : self.table.contents,
				"istext"     : self.table.istext,
				"fhash"      : self.table.fhash,
				"mimetype"   : self.table.mimetype,
				"fspath"     : self.table.fspath,
				"distance"   : self.table.distance,
				"walklimit"  : self.table.walklimit,
			}


	##############################################################################################################################################
	#
	#
	#	########  ########     ######## ##     ## ##    ##  ######  ######## ####  #######  ##    ##  ######
	#	##     ## ##     ##    ##       ##     ## ###   ## ##    ##    ##     ##  ##     ## ###   ## ##    ##
	#	##     ## ##     ##    ##       ##     ## ####  ## ##          ##     ##  ##     ## ####  ## ##
	#	##     ## ########     ######   ##     ## ## ## ## ##          ##     ##  ##     ## ## ## ##  ######
	#	##     ## ##     ##    ##       ##     ## ##  #### ##          ##     ##  ##     ## ##  ####       ##
	#	##     ## ##     ##    ##       ##     ## ##   ### ##    ##    ##     ##  ##     ## ##   ### ##    ##
	#	########  ########     ##        #######  ##    ##  ######     ##    ####  #######  ##    ##  ######
	#
	#
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

		if 'url' in kwargs:

			cols.append(self.table.netloc)
			vals.append(urllib.parse.urlparse(kwargs['url']).netloc.lower())

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
	def insertIntoDb(self, commit=True, cursor=None, **kwargs):
		query, queryArguments = self.sqlBuildInsertArgs(returning=[self.table.dbid], **kwargs)

		if self.QUERY_DEBUG:
			print("Query = ", query)
			print("Args = ", queryArguments)


		if cursor:
			cursor.execute(query, queryArguments)
			ret = cursor.fetchone()
			try:
				self.insertDelta(cursor=cursor, **kwargs)
			except ValueError:
				self.log.error("Error when updating change stats:")
				for line in traceback.format_exc().split("\n"):
					self.log.error(line)
		else:
			with self.transaction(commit=commit) as cur:
				cur.execute(query, queryArguments)
				ret = cur.fetchone()
				try:
					self.insertDelta(cursor=cur, **kwargs)
				except ValueError:
					self.log.error("Error when updating change stats:")
					for line in traceback.format_exc().split("\n"):
						self.log.error(line)

		if self.QUERY_DEBUG:
			print("Query ret = ", ret)

		return ret[0]


	def generateUpdateQuery(self, **kwargs):

		cols = []
		vals = []

		# By default, take ownership of any pages we're operating on by setting it's src key to us
		if not 'src' in kwargs:
			cols.append(self.table.src)
			vals.append(self.tableKey)

		if 'url' in kwargs:
			cols.append(self.table.netloc)
			vals.append(urllib.parse.urlparse(kwargs['url']).netloc.lower())

		if "dbid" in kwargs:
			where = (self.table.dbid == kwargs.pop('dbid'))
		elif "url" in kwargs:
			where = (self.table.url == kwargs.pop('url'))
		else:
			raise ValueError("GenerateUpdateQuery must be passed a single unique column identifier (either dbId or url)")

		# Extract and insert the netloc if needed.
		if 'url' in kwargs:
			print("Urlparse!")
			cols.append(self.table.netloc)
			vals.append(urllib.parse.urlparse(kwargs['url']).netloc.lower())


		for key, val in kwargs.items():
			key = key.lower()

			if key not in self.colMap:
				raise ValueError("Invalid column name for insert! '%s'" % key)
			cols.append(self.colMap[key])
			vals.append(val)

		query = self.table.update(columns=cols, values=vals, where=where)
		query, params = tuple(query)

		return query, params

	def updateDistance(self, cur, distance, **kwargs):

		if "dbid" in kwargs:
			where = (self.table.dbid == kwargs.pop('dbid'))
		elif "url" in kwargs:
			where = (self.table.url == kwargs.pop('url'))
		else:
			raise ValueError("GenerateUpdateQuery must be passed a single unique column identifier (either dbId or url)")

		cols = [self.table.distance]
		vals = [sqlc.Least(distance, self.table.distance)]

		query = self.table.update(columns=cols, values=vals, where=where)
		query, params = tuple(query)

		if self.QUERY_DEBUG:
			print("Query = ", query)
			print("Args = ", params)
		cur.execute(query, params)

	# Update entry with key sourceUrl with values **kwargs
	# kwarg names are checked for validity, and to prevent possiblity of sql injection.
	def updateDbEntry(self, commit=True, cursor=None, **kwargs):

		distance = None
		if 'distance' in kwargs:
			distance = kwargs.pop('distance')


		# Apparently passing a dict as ** does (at least) a shallow copy
		# Therefore, we can ignore the fact that generateUpdateQuery
		# will then permute it's copy of the kwargs, and just use it again
		# for the call to updateDistance
		query, queryArguments = self.generateUpdateQuery(**kwargs)

		if self.QUERY_DEBUG:
			print("Query = ", query)
			print("Args = ", queryArguments)

		if cursor:
			if distance != None:
				self.updateDistance(cursor, distance, **kwargs)
			cursor.execute(query, queryArguments)
			try:
				self.insertDelta(cursor=cursor, **kwargs)
			except ValueError:
				self.log.error("Error when updating change stats:")
				for line in traceback.format_exc().split("\n"):
					self.log.error(line)

		else:
			with self.transaction(commit=commit) as cur:
				if distance != None:
					self.updateDistance(cur, distance, **kwargs)
				cur.execute(query, queryArguments)
				try:
					self.insertDelta(cursor=cur, **kwargs)
				except ValueError:
					self.log.error("Error when updating change stats:")
					for line in traceback.format_exc().split("\n"):
						self.log.error(line)



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

		with self.transaction(commit=commit) as cur:
			cur.execute(query, args)





	def getRowsByValue(self, limitByKey=True, cursor=None, **kwargs):
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

		if cursor:

			cursor.execute(query, quargs)
			rets = cursor.fetchall()
		else:
			with self.transaction() as cur:
				#wrap queryies in transactions so we don't have hanging db handles.
				cur.execute(query, quargs)
				rets = cur.fetchall()


		retL = []
		for row in rets:

			keys = ['dbid', 'src', 'dlstate', 'url', 'title', 'series', 'contents', 'istext', 'fhash', 'mimetype', 'fspath']
			retL.append(dict(zip(keys, row)))
		return retL

	def getRowByValue(self, cursor=None, **kwargs):
		rows = self.getRowsByValue(cursor=cursor, **kwargs)
		if len(rows) == 1:
			return rows.pop()
		if len(rows) == 0:
			return None
		else:
			raise ValueError("Got multiple rows for selection. Wat?")



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



	def saveFile(self, url, mimetype, fileName, content):


		hadFile = False
		# Yeah, I'm hashing twice in lots of cases. Bite me
		fHash = self.getHash(content)


		# Look for existing files with the same MD5sum. If there are any, just point the new file at the
		# fsPath of the existing one, rather then creating a new file on-disk.
		with self.transaction() as cur:
			cur.execute("SELECT fspath  FROM {tableName} WHERE fhash=%s;".format(tableName=self.tableName), (fHash, ))
			row = cur.fetchone()
			if row:
				self.log.info("Already downloaded file. Not creating duplicates.")
				hadFile = True
				fqPath = row[0]

		with self.transaction() as cur:

			cur.execute("SELECT dbid, fspath, contents, mimetype  FROM {tableName} WHERE url=%s;".format(tableName=self.tableName), (url, ))
			row = cur.fetchone()
			if not row:
				self.log.critical("Failure when saving file for URL '%s'", url)
				self.log.critical("File name: '%s'", fileName)
				return

			dbid, dummy_havePath, dummy_haveCtnt, dummy_haveMime = row
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
				with self.transaction() as cur:
					newRowDict = {"dlstate" : -1}
					self.updateDbEntry(url=url, commit=False, **newRowDict)


	def getToDo(self, distance):

		# Retreiving todo items must be atomic, so we lock for that.
		with self.dbLock:
			with self.transaction() as cur:

				cur.execute('''SELECT dbid, url, distance FROM {tableName} WHERE dlstate=%s AND src=%s AND distance < %s ORDER BY distance ASC, istext ASC  LIMIT 1;'''.format(tableName=self.tableName), (0, self.tableKey, distance))
				row = cur.fetchone()

				# print(('''SELECT dbid, url, distance FROM {tableName} WHERE dlstate=%s AND src=%s AND distance < %s ORDER BY istext ASC LIMIT 1;'''.format(tableName=self.tableName) % (0, self.tableKey, distance)))
				# print(row)

				if not row:
					return False
				else:
					dbid, url, itemDistance = row
					cur.execute('UPDATE {tableName} SET dlstate=%s WHERE dbid=%s;'.format(tableName=self.tableName), (1, dbid))

		if not url.startswith("http"):
			raise ValueError("Non HTTP URL in database: '%s'!" % url)
		return url, itemDistance


	def getTodoCount(self):
		with self.dbLock:
			with self.transaction() as cur:

				cur.execute('''SELECT COUNT(*) FROM {tableName} WHERE dlstate=%s AND src=%s;'''.format(tableName=self.tableName), (0, self.tableKey))
				row = cur.fetchone()

				return row[0]




	def resetStuckItems(self):
		self.log.info("Resetting stuck downloads in DB")
		with self.transaction() as cur:
			cur.execute('''UPDATE {tableName} SET dlState=0 WHERE dlState=1 AND src=%s'''.format(tableName=self.tableName), (self.tableKey, ))
		self.log.info("Download reset complete")

	# Override to filter items that get
	def changeFilter(self, url, title, changePercentage):
		return False

	def insertChangeStats(self, url, changePercentage, title, cursor=None):

		# Skip title cruft on baka-tsuki
		if self.changeFilter(url, title, changePercentage):
			return

		# If we weren't passed a title, look it up from the DB.
		if not title:
			self.log.warning("ChangeStat call without title parameter passed!")
			row = self.getRowByValue(url=url, cursor=cursor)
			if row and row['title']:
				title = row['title']
			else:
				title = url


		query = '''INSERT INTO {changeTable} (src, url, change, title, changeDate) VALUES (%s, %s, %s, %s, %s)'''.format(changeTable=self.changeTableName)
		values = (self.tableKey, url, changePercentage, title, time.time())
		if cursor:
			cursor.execute(query, values)
		else:
			with self.transaction() as cur:
				cur.execute(query, values)


	##############################################################################################################################################
	# Higher level DB Interfacing
	##############################################################################################################################################


	def upsert(self, pgUrl, commit=True, **kwargs):
		if 'url' in kwargs and 'drive_web' in kwargs['url']:
			self.log.error('')
			self.log.error('')
			self.log.error("WAT")
			self.log.error('')
			self.log.error(traceback.format_stack())
			self.log.error('')


		if 'url' in kwargs and not kwargs['url'].startswith("http"):
			self.log.error('')
			self.log.error('')
			self.log.error("WAT")
			self.log.error('')
			self.log.error(traceback.format_stack())
			self.log.error('')


		# print("Upserting!")

		with self.transaction(commit=commit) as cur:
			# Do everything in one transaction

			try:
				self.insertIntoDb(url=pgUrl, cursor=cur, **kwargs)

			except psycopg2.IntegrityError:
				if kwargs:
					cur.execute("ROLLBACK")
					cur.execute("BEGIN")
					self.updateDbEntry(url=pgUrl, cursor=cur, **kwargs)
		# print("Upserted")

	def insertDelta(self, cursor=None, **kwargs):

		if 'istext' in kwargs and not kwargs['istext']:
			return

		if not 'contents' in kwargs:
			return

		if 'url' in kwargs:
			old = self.getRowByValue(url=kwargs['url'], cursor=cursor)
		elif 'dbid' in kwargs:
			old = self.getRowByValue(dbid=kwargs['dbid'], cursor=cursor)
		else:
			raise ValueError("No identifying info in insertDelta call!")




		if 'title' in kwargs and kwargs['title']:
			title = kwargs['title']
		else:
			if not old:
				self.log.error("empty reference in changestat? kwargs: %s", kwargs)
				return
			if not old['mimetype']:
				self.log.warn("Skipping change stats for item because of mimetype of '%s'", old['mimetype'])
				return
			if not old['mimetype'] in ['text/html', 'text/plain']:
				self.log.warn("Skipping change stats for item because of mimetype of '%s'", old['mimetype'])
				return

			title = old['title']

		if not title:
			self.log.error("No title found for item at url:")
			self.log.error(old['url'])
			title = ''


		item = kwargs['url'] if 'url' in kwargs else kwargs['dbid']
		if not old:
			self.log.error("Couldn't find old version of item '%s'", item)
			old = {}
			old['contents'] = ''
			if 'url' in kwargs:
				old['url'] = kwargs['url']
			else:
				raise ValueError('The initial ChangeStat value must be inserted by URL!')



		if old['contents'] == None:
			old['contents'] = ''

		oldStr = str(old['contents'])
		newStr = str(kwargs['contents'])

		# self.log.info("Calculating edit-distance")
		# print("String lengths", len(oldStr), len(newStr))

		lChange = abs(len(oldStr) - len(newStr))
		lTotal = max((len(oldStr), len(newStr)))
		self.log.info("Coarse length change: %s (mean: %s)", lChange, int(sum((len(oldStr), len(newStr)))/2 ))
		# distance = lv.distance(oldStr, newStr)
		# distance = 0
		# self.log.info("Done")
		# space = min((len(oldStr), len(newStr)))

		if lTotal == 0:
			lTotal = 1

		change = (lChange / lTotal) * 100
		change = min((change, 100))
		self.log.info("Percent change in page contents: %s", change)

		self.insertChangeStats(old['url'], change, title=title, cursor=cursor)


	def getHash(self, fCont):

		m = hashlib.md5()
		m.update(fCont)
		return m.hexdigest()

