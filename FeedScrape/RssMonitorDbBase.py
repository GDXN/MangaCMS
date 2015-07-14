


import runStatus
runStatus.preloadDicts = False

# import Levenshtein as lv


import sql.conditionals as sqlc
import sql.aggregate as sqla
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

		self.table       = None
		self.cols        = None
		self.validKwargs = None
		self.colMap      = None


		# I have to wrap the DB in locks, since two pages may return
		# identical links at the same time.
		# Using transactions could result in collisions, so we lock.
		# Most of the time is spent in processing pages anyways
		self.dbLock = threading.Lock()

		self.checkInitRssDb()

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
												srcname     TEXT NOT NULL,
												feedurl     TEXT NOT NULL,

												contenturl  TEXT NOT NULL,
												contentid   TEXT NOT NULL UNIQUE,
												title       TEXT,
												contents    TEXT,
												author      TEXT,

												tags        JSON,

												updated     DOUBLE PRECISION DEFAULT -1,
												published   DOUBLE PRECISION NOT NULL

												);'''.format(tableName=self.tableName))

			# 'entryHash' is going to be the feed URL + entry title hashed?

			cur.execute("SELECT relname FROM pg_class;")
			haveIndexes = cur.fetchall()
			haveIndexes = [index[0] for index in haveIndexes]

			indexes = [
				("%s_srcname_index"    % self.tableName, self.tableName, '''CREATE INDEX %s ON %s (srcname    );'''  ),
				("%s_feedurl_index"    % self.tableName, self.tableName, '''CREATE INDEX %s ON %s (feedurl    );'''  ),
				("%s_contenturl_index" % self.tableName, self.tableName, '''CREATE INDEX %s ON %s (contenturl );'''  ),
				("%s_contentid_index"  % self.tableName, self.tableName, '''CREATE INDEX %s ON %s (contentid  );'''  ),
				("%s_title_index"      % self.tableName, self.tableName, '''CREATE INDEX %s ON %s (title      );'''  ),
				("%s_title_trigram"    % self.tableName, self.tableName, '''CREATE INDEX %s ON %s USING gin (title gin_trgm_ops);'''  ),
			]

			for name, table, nameFormat in indexes:
				if not name.lower() in haveIndexes:
					cur.execute(nameFormat % (name, table))

			print("Instantiation complete")

		self.log.info("Retreived page database created")


		self.table = sql.Table(self.tableName.lower())
		self.cols = (
			self.table.dbid,
			self.table.srcname,
			self.table.feedurl,
			self.table.contenturl,
			self.table.contentid,
			self.table.title,
			self.table.contents,
			self.table.author,
			self.table.tags,
			self.table.updated,
			self.table.published,
		)


		self.validKwargs = [
					'dbid',
					'srcname',
					'feedurl',
					'contenturl',
					'contentid',
					'title',
					'contents',
					'author',
					'tags',
					'updated',
					'published'
				]


		self.colMap = {
			'dbid'        : self.table.dbid,
			'srcname'     : self.table.srcname,
			'feedurl'     : self.table.feedurl,
			'contenturl'  : self.table.contenturl,
			'contentid'   : self.table.contentid,
			'title'       : self.table.title,
			'contents'    : self.table.contents,
			'author'      : self.table.author,
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

		cols = []
		vals = []

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
			kwargs["srcname"] = self.tableKey


		where = self.sqlBuildConditional(**kwargs)

		wantCols = (
				self.table.dbid,
				self.table.srcname,
				self.table.feedurl,
				self.table.contenturl,
				self.table.contentid,
				self.table.title,
				self.table.contents,
				self.table.author,
				self.table.tags,
				self.table.updated,
				self.table.published,
			)

		query = self.table.select(*wantCols, order_by=sql.Desc(self.table.dbid), where=where)

		query, quargs = tuple(query)

		if self.QUERY_DEBUG:
			print("Query = ", query)
			print("args = ", quargs)


		with self.transaction() as cur:
			cur.execute(query, quargs)
			rets = cur.fetchall()




		retL = []
		for row in rets:

			keys = ['dbid', 'srcname', 'feedurl', 'contenturl', 'contentid', 'title', 'contents', 'author', 'tags', 'updated', 'published']
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


	def itemInDB(self, **kwargs):
		return bool(self.getNumberOfRows(**kwargs))


	def getNumberOfRows(self, where=None, **kwargs):
		if not where:
			where = self.sqlBuildConditional(**kwargs)

		query = self.table.select(sqla.Count(sql.Literal(1)), where=where)

		query, params = tuple(query)

		if self.QUERY_DEBUG:
			self.log.info("Query = '%s'", query)
			self.log.info("Args = '%s'", params)


		with self.transaction() as cur:
			cur.execute(query, params)
			ret = cur.fetchone()

		return ret[0]

	def getHash(self, fCont):

		m = hashlib.md5()
		m.update(fCont)
		return m.hexdigest()
