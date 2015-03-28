


import runStatus
runStatus.preloadDicts = False

# import Levenshtein as lv


import sql.conditionals as sqlc
import settings
import abc
import urllib.parse
import functools
import operator as opclass

import sql
# import sql.operators as sqlo


import hashlib
import psycopg2
import os
import threading
import os.path

import nameTools



import DbBase




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


class RssDbBase(DbBase.DbBase, metaclass=abc.ABCMeta):

	# Abstract class (must be subclassed)
	__metaclass__ = abc.ABCMeta

	tableName = 'rss_monitor'

	QUERY_DEBUG = False


	@abc.abstractproperty
	def tableKey(self):
		pass

	def __init__(self):
		super().__init__()

		print('wat')

		self.table       = None
		self.cols        = None
		self.validKwargs = None
		self.colMap      = None


		# I have to wrap the DB in locks, since two pages may return
		# identical links at the same time.
		# Using transactions could result in collisions, so we lock.
		# Most of the time is spent in processing pages anyways
		self.dbLock = threading.Lock()

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


	def checkInitRssDb(self):
		with self.transaction() as cur:

			cur.execute('''CREATE TABLE IF NOT EXISTS {tableName} (
												dbid        SERIAL PRIMARY KEY,
												src         TEXT NOT NULL,

												linkUrl     TEXT NOT NULL UNIQUE,
												title       TEXT,
												contents    TEXT,
												contentHash TEXT NOT NULL,
												author      TEXT,

												tags        JSON,

												updated     DOUBLE PRECISION DEFAULT -1,
												published   DOUBLE PRECISION NOT NULL,

												);'''.format(tableName=self.tableName))

			# 'entryHash' is going to be the feed URL + entry title hashed?

			cur.execute("SELECT relname FROM pg_class;")
			haveIndexes = cur.fetchall()
			haveIndexes = [index[0] for index in haveIndexes]

			indexes = [
				("%s_source_index"     % self.tableName, self.tableName, '''CREATE INDEX %s ON %s (src     );'''  ),
				("%s_linkUrl_index"    % self.tableName, self.tableName, '''CREATE INDEX %s ON %s (linkUrl );'''  ),
				("%s_istext_index"     % self.tableName, self.tableName, '''CREATE INDEX %s ON %s (istext  );'''  ),
				("%s_linkUrl_index"    % self.tableName, self.tableName, '''CREATE INDEX %s ON %s (linkUrl );'''  ),
				("%s_title_index"      % self.tableName, self.tableName, '''CREATE INDEX %s ON %s (title   );'''  ),
				("%s_title_trigram"    % self.tableName, self.tableName, '''CREATE INDEX %s ON %s USING gin (title gin_trgm_ops);'''  ),
			]

			for name, table, nameFormat in indexes:
				if not name.lower() in haveIndexes:
					cur.execute(nameFormat % (name, table))

		self.log.info("Retreived page database created")
		with self.transaction() as cur:


			self.table = sql.Table(self.tableName.lower())
			self.cols = (
				self.table.dbid,
				self.table.src,
				self.table.guid,
				self.table.title,
				self.table.contents,
				self.table.contentHash,
				self.table.author,
				self.table.linkUrl,
				self.table.tags,
				self.table.updated,
				self.table.published,
			)


			self.validKwargs = ['dbid', 'src', 'guid', 'title', 'contents', 'contentHash', 'author', 'linkUrl', 'tags', 'updated', 'published']


			self.colMap = {
				'dbid'        : self.table.dbid,
				'src'         : self.table.src,
				'guid'        : self.table.guid,
				'title'       : self.table.title,
				'contents'    : self.table.contents,
				'contentHash' : self.table.contentHash,
				'author'      : self.table.author,
				'linkUrl'     : self.table.linkUrl,
				'tags'        : self.table.tags,
				'updated'     : self.table.updated,
				'published'   : self.table.published,
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

		with self.transaction(commit=commit) as cur:
			cur.execute(query, queryArguments)
			ret = cur.fetchone()

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
	def updateDbEntry(self, commit=True, **kwargs):

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

		with self.transaction(commit=commit) as cur:
			if distance != None:
				self.updateDistance(cur, distance, **kwargs)
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

		with self.transaction(commit=commit) as cur:
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


		with self.transaction(commit=commit) as cur:
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

		with self.transaction() as cur:

			# Look for existing files with the same MD5sum. If there are any, just point the new file at the
			# fsPath of the existing one, rather then creating a new file on-disk.
			cur.execute("SELECT fspath  FROM {tableName} WHERE fhash=%s;".format(tableName=self.tableName), (fHash, ))
			row = cur.fetchone()
			if row:
				self.log.info("Already downloaded file. Not creating duplicates.")
				hadFile = True
				fqPath = row[0]


			cur.execute("SELECT dbid, fspath, contents, mimetype  FROM {tableName} WHERE url=%s;".format(tableName=self.tableName), (url, ))
			row = cur.fetchone()
			if not row:
				self.log.critical("Failure when saving file for URL '%s'", url)
				self.log.critical("File name: '%s'", fileName)
				return

			dbid = row[0]
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

				newRowDict = {"dlstate" : -1}
				self.updateDbEntry(url=url, commit=False, **newRowDict)


	def getToDo(self, distance):

		# Retreiving todo items must be atomic, so we lock for that.
		with self.dbLock:
			with self.transaction() as cur:

				cur.execute('''SELECT dbid, url, distance FROM {tableName} WHERE dlstate=%s AND src=%s AND distance < %s ORDER BY istext ASC LIMIT 1;'''.format(tableName=self.tableName), (0, self.tableKey, distance))
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
		with self.transaction() as cur:

			cur.execute('''SELECT COUNT(*) FROM {tableName} WHERE dlstate=%s AND src=%s;'''.format(tableName=self.tableName), (0, self.tableKey))
			row = cur.fetchone()

			return row[0]




	def resetStuckItems(self):
		self.log.info("Resetting stuck downloads in DB")

		with self.transaction() as cur:
			cur.execute('''UPDATE {tableName} SET dlState=0 WHERE dlState=1 AND src=%s'''.format(tableName=self.tableName), (self.tableKey, ))
		self.log.info("Download reset complete")


	##############################################################################################################################################
	# Higher level DB Interfacing
	##############################################################################################################################################


	def upsert(self, pgUrl, commit=True, **kwargs):

		try:
			self.insertIntoDb(commit=commit, url=pgUrl, **kwargs)

		except psycopg2.IntegrityError:
			if kwargs:
				self.updateDbEntry(commit=commit, url=pgUrl, **kwargs)



	def getHash(self, fCont):

		m = hashlib.md5()
		m.update(fCont)
		return m.hexdigest()
