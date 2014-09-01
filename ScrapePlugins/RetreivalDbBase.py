

import logging
import psycopg2
import abc

import threading
import settings
import os
import traceback

import nameTools as nt
import ScrapePlugins.DbBase

# Turn on to print all db queries to STDOUT before running them.
# Intended for debugging DB interactions.
# Excessively verbose otherwise.
QUERY_DEBUG = False

class ScraperDbBase(ScrapePlugins.DbBase.DbBase):

	# Abstract class (must be subclassed)
	__metaclass__ = abc.ABCMeta



	@abc.abstractmethod
	def pluginName(self):
		return None

	@abc.abstractmethod
	def loggerPath(self):
		return None

	@abc.abstractmethod
	def dbName(self):
		return None

	@abc.abstractmethod
	def tableKey(self):
		return None

	@abc.abstractmethod
	def tableName(self):
		return None


	# ---------------------------------------------------------------------------------------------------------------------------------------------------------
	# Messy hack to do log indirection so I can inject thread info into log statements, and give each thread it's own DB handle.
	# Basically, intercept all class member accesses, and if the access is to either the logging interface, or the DB,
	# look up/create a per-thread instance of each, and return that
	#
	# The end result is each thread just uses `self.conn` and `self.log` as normal, but actually get a instance of each that is
	# specifically allocated for just that thread
	#
	# ~~Sqlite 3 doesn't like having it's DB handles shared across threads. You can turn the checking off, but I had
	# db issues when it was disabled. This is a much more robust fix~~
	#
	# Migrated to PostgreSQL. We'll see how that works out.
	#
	# The log indirection is just so log statements include their originating thread. I like lots of logging.
	#
	# ---------------------------------------------------------------------------------------------------------------------------------------------------------

	def __getattribute__(self, name):

		threadName = threading.current_thread().name
		if name == "log" and "Thread-" in threadName:
			if threadName not in self.loggers:
				self.loggers[threadName] = logging.getLogger("Main.%s.Thread-%d" % (self.loggerPath, self.lastLoggerIndex))
				self.lastLoggerIndex += 1
			return self.loggers[threadName]


		elif name == "conn":
			if threadName not in self.dbConnections:
				self.dbConnections[threadName] = psycopg2.connect(host=settings.PSQL_IP, dbname=settings.DATABASE_DB_NAME, user=settings.DATABASE_USER,password=settings.DATABASE_PASS)
				self.dbConnections[threadName].autocommit = True
			return self.dbConnections[threadName]


		else:
			return object.__getattribute__(self, name)


	validKwargs = ["dlState", "sourceUrl", "retreivalTime", "lastUpdate", "sourceId", "seriesName", "fileName", "originName", "downloadPath", "flags", "tags", "note"]

	def __init__(self):

		self.loggers = {}
		self.dbConnections = {}
		self.lastLoggerIndex = 1

		self.log = logging.getLogger(self.loggerPath)
		self.log.info("Loading %s Runner BaseClass", self.pluginName)
		self.openDB()
		self.checkInitPrimaryDb()

	# Deferred to special hook in __getattribute__ that provides separate
	# db interfaces to each thread.
	def openDB(self):
		pass


	def closeDB(self):
		self.log.info("Closing DB...",)
		self.conn.close()
		self.log.info("DB Closed")


	# ---------------------------------------------------------------------------------------------------------------------------------------------------------
	# Filesystem stuff
	# ---------------------------------------------------------------------------------------------------------------------------------------------------------


	# either locate or create a directory for `seriesName`.
	# If the directory cannot be found, one will be created.
	# Returns {pathToDirectory string}, {HadToCreateDirectory bool}
	def locateOrCreateDirectoryForSeries(self, seriesName):


		canonSeriesName = nt.getCanonicalMangaUpdatesName(seriesName)
		safeBaseName = nt.makeFilenameSafe(canonSeriesName)


		if canonSeriesName in nt.dirNameProxy:
			self.log.info("Have target dir for '%s' Dir = '%s'", canonSeriesName, nt.dirNameProxy[canonSeriesName]['fqPath'])
			return nt.dirNameProxy[canonSeriesName]["fqPath"], False
		else:
			self.log.info("Don't have target dir for: %s, full name = %s", canonSeriesName, seriesName)
			targetDir = os.path.join(settings.baseDir, safeBaseName)
			if not os.path.exists(targetDir):
				try:
					os.makedirs(targetDir)
					return targetDir, True

				except OSError:
					self.log.critical("Directory creation failed?")
					self.log.critical(traceback.format_exc())
			else:
				self.log.warning("Directory not found in dir-dict, but it exists!")
				self.log.warning("Directory-Path: %s", targetDir)
				self.log.warning("Base series name: %s", seriesName)
				self.log.warning("Canonized series name: %s", canonSeriesName)
				self.log.warning("Safe canonized name: %s", safeBaseName)
			return targetDir, False


	# ---------------------------------------------------------------------------------------------------------------------------------------------------------
	# DB Tools
	# ---------------------------------------------------------------------------------------------------------------------------------------------------------


	def buildInsertArgs(self, **kwargs):

		# Pre-populate with the table keys.
		keys = ["sourceSite"]
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
	def insertIntoDb(self, commit=True, **kwargs):


		keysStr, valuesStr, queryArguments = self.buildInsertArgs(**kwargs)

		query = '''INSERT INTO {tableName} ({keys}) VALUES ({values});'''.format(tableName=self.tableName, keys=keysStr, values=valuesStr)

		if QUERY_DEBUG:
			print("Query = ", query)
			print("Args = ", queryArguments)

		with self.conn.cursor() as cur:

			if commit:
				cur.execute("BEGIN;")

			cur.execute(query, queryArguments)

			if commit:
				cur.execute("COMMIT;")



	# Update entry with key sourceUrl with values **kwargs
	# kwarg names are checked for validity, and to prevent possiblity of sql injection.
	def updateDbEntry(self, sourceUrl, commit=True, **kwargs):

		# Patch series name.
		if "seriesName" in kwargs and kwargs["seriesName"]:
			kwargs["seriesName"] = nt.getCanonicalMangaUpdatesName(kwargs["seriesName"])

		# print("Updating", self.getRowByValue(sourceUrl=sourceUrl), kwargs)
		queries = []
		qArgs = []
		for key in kwargs.keys():
			if key not in self.validKwargs:
				raise ValueError("Invalid keyword argument: %s" % key)
			else:
				queries.append("{k}=%s".format(k=key))
				qArgs.append(kwargs[key])

		qArgs.append(sourceUrl)
		qArgs.append(self.tableKey)
		column = ", ".join(queries)


		query = '''UPDATE {tableName} SET {v} WHERE sourceUrl=%s AND sourceSite=%s;'''.format(tableName=self.tableName, v=column)

		if QUERY_DEBUG:
			print("Query = ", query)
			print("Args = ", qArgs)

		with self.conn.cursor() as cur:

			if commit:
				cur.execute("BEGIN;")

			cur.execute(query, qArgs)

			if commit:
				cur.execute("COMMIT;")

		# print("Updating", self.getRowByValue(sourceUrl=sourceUrl))

	# Update entry with key sourceUrl with values **kwargs
	# kwarg names are checked for validity, and to prevent possiblity of sql injection.
	def updateDbEntryById(self, rowId, commit=True, **kwargs):

		# Patch series name.
		if "seriesName" in kwargs and kwargs["seriesName"]:
			kwargs["seriesName"] = nt.getCanonicalMangaUpdatesName(kwargs["seriesName"])

		queries = []
		qArgs = []
		for key in kwargs.keys():
			if key not in self.validKwargs:
				raise ValueError("Invalid keyword argument: %s" % key)
			else:
				queries.append("{k}=%s".format(k=key))
				qArgs.append(kwargs[key])

		qArgs.append(rowId)
		qArgs.append(self.tableKey)
		column = ", ".join(queries)


		query = '''UPDATE {tableName} SET {v} WHERE dbId=%s AND sourceSite=%s;'''.format(tableName=self.tableName, v=column)

		if QUERY_DEBUG:
			print("Query = ", query)
			print("Args = ", qArgs)

		with self.conn.cursor() as cur:

			if commit:
				cur.execute("BEGIN;")

			cur.execute(query, qArgs)

			if commit:
				cur.execute("COMMIT;")

		# print("Updating", self.getRowByValue(sourceUrl=sourceUrl))


	def deleteRowsByValue(self, commit=True, **kwargs):
		if len(kwargs) != 1:
			raise ValueError("getRowsByValue only supports calling with a single kwarg", kwargs)
		validCols = ["dbId", "sourceUrl", "dlState"]
		key, val = kwargs.popitem()
		if key not in validCols:
			raise ValueError("Invalid column query: %s" % key)


		query = '''DELETE FROM {tableName} WHERE {key}=%s AND sourceSite=%s;'''.format(tableName=self.tableName, key=key)
		# print("Query = ", query)

		if QUERY_DEBUG:
			print("Query = ", query)
			print("Args = ", (val, self.tableKey))

		with self.conn.cursor() as cur:

			if commit:
				cur.execute("BEGIN;")

			cur.execute(query, (val, self.tableKey))

			if commit:
				cur.execute("COMMIT;")


	def getRowsByValue(self, limitByKey=True, **kwargs):
		if len(kwargs) != 1:
			raise ValueError("getRowsByValue only supports calling with a single kwarg" % kwargs)
		validCols = ["dbId", "sourceUrl", "dlState", "originName"]
		key, val = kwargs.popitem()
		if key not in validCols:
			raise ValueError("Invalid column query: %s" % key)


		# HACKY alternate query for limitByKey. Fix?
		if limitByKey:
			query = '''SELECT dbId,
								dlState,
								sourceUrl,
								retreivalTime,
								lastUpdate,
								sourceId,
								seriesName,
								fileName,
								originName,
								downloadPath,
								flags,
								tags,
								note
								FROM {tableName} WHERE {key}=%s AND sourceSite=%s ORDER BY retreivalTime DESC;'''.format(tableName=self.tableName, key=key)
			quargs = (val, self.tableKey)

		else:
			query = '''SELECT dbId,
								dlState,
								sourceUrl,
								retreivalTime,
								lastUpdate,
								sourceId,
								seriesName,
								fileName,
								originName,
								downloadPath,
								flags,
								tags,
								note
								FROM {tableName} WHERE {key}=%s ORDER BY retreivalTime DESC;'''.format(tableName=self.tableName, key=key)
			quargs = (val, )


		if QUERY_DEBUG:
			print("Query = ", query)
			print("args = ", quargs)

		with self.conn.cursor() as cur:
			cur.execute(query, quargs)
			rets = cur.fetchall()



		retL = []
		for row in rets:

			keys = ["dbId", "dlState", "sourceUrl", "retreivalTime", "lastUpdate", "sourceId", "seriesName", "fileName", "originName", "downloadPath", "flags", "tags", "note"]
			retL.append(dict(zip(keys, row)))
		return retL

	# Insert new tags specified as a string kwarg (tags="tag Str") into the tags listing for the specified item
	def addTags(self, **kwargs):
		validCols = ["dbId", "sourceUrl", "dlState"]
		if not any([name in kwargs for name in validCols]):
			raise ValueError("addTags requires at least one fully-qualified argument (%s). Passed args = '%s'" % (validCols, kwargs))

		if not "tags" in kwargs:
			raise ValueError("You have to specify tags you want to add as a kwarg! '%s'" % (kwargs))

		tags = kwargs.pop("tags")
		row = self.getRowByValue(**kwargs)
		if not row:
			raise ValueError("Row specified does not exist!")

		if row["tags"]:
			existingTags = set(row["tags"].split(" "))
		else:
			existingTags = set()

		newTags = set(tags.split(" "))

		tags = existingTags | newTags

		tagStr = " ".join(tags)
		while "  " in tagStr:
			tagStr = tagStr.replace("  ", " ")

		self.updateDbEntry(row["sourceUrl"], tags=tagStr)


	# Convenience crap.
	def getRowByValue(self, **kwargs):
		rows = self.getRowsByValue(**kwargs)
		if not rows:
			return []
		else:
			return rows.pop(0)


	def resetStuckItems(self):
		self.log.info("Resetting stuck downloads in DB")
		with self.conn.cursor() as cur:
			cur.execute('''UPDATE {tableName} SET dlState=0 WHERE dlState=1 AND sourceSite=%s'''.format(tableName=self.tableName), (self.tableKey, ))
		self.conn.commit()
		self.log.info("Download reset complete")


	# ---------------------------------------------------------------------------------------------------------------------------------------------------------
	# DB Management
	# ---------------------------------------------------------------------------------------------------------------------------------------------------------

	def checkInitPrimaryDb(self):
		with self.conn.cursor() as cur:

			cur.execute('''CREATE TABLE IF NOT EXISTS {tableName} (
												dbId          SERIAL PRIMARY KEY,
												sourceSite    TEXT NOT NULL,
												dlState       INTEGER NOT NULL,
												sourceUrl     text UNIQUE NOT NULL,
												retreivalTime double precision NOT NULL,
												lastUpdate    double precision DEFAULT 0,
												sourceId      text,
												seriesName    CITEXT,
												fileName      text,
												originName    text,
												downloadPath  text,
												flags         CITEXT,
												tags          CITEXT,
												note          text);'''.format(tableName=self.tableName))


			cur.execute("SELECT relname FROM pg_class;")
			haveIndexes = cur.fetchall()
			haveIndexes = [index[0] for index in haveIndexes]



			indexes = [
				("%s_source_index"           % self.tableName, self.tableName, '''CREATE INDEX %s ON %s (sourceSite)'''                                             ),
				("%s_time_index"             % self.tableName, self.tableName, '''CREATE INDEX %s ON %s (retreivalTime)'''                                          ),
				("%s_lastUpdate_index"       % self.tableName, self.tableName, '''CREATE INDEX %s ON %s (lastUpdate)'''                                             ),
				("%s_url_index"              % self.tableName, self.tableName, '''CREATE INDEX %s ON %s (sourceUrl)'''                                              ),
				("%s_seriesName_index"       % self.tableName, self.tableName, '''CREATE INDEX %s ON %s (seriesName )'''                                            ),
				("%s_tags_index"             % self.tableName, self.tableName, '''CREATE INDEX %s ON %s (tags       )'''                                            ),
				("%s_flags_index"            % self.tableName, self.tableName, '''CREATE INDEX %s ON %s (flags      )'''                                            ),
				("%s_dlState_index"          % self.tableName, self.tableName, '''CREATE INDEX %s ON %s (dlState)'''                                                ),
				("%s_originName_index"       % self.tableName, self.tableName, '''CREATE INDEX %s ON %s (originName)'''                                             ),
				("%s_aggregate_index"        % self.tableName, self.tableName, '''CREATE INDEX %s ON %s (seriesName, retreivalTime, dbId)'''                        ),
				('%s_special_full_idx'       % self.tableName, self.tableName, '''CREATE INDEX %s ON %s (retreivaltime DESC, seriesName DESC, dbid);'''             ),
				('%s_special_granulated_idx' % self.tableName, self.tableName, '''CREATE INDEX %s ON %s (sourceSite, retreivaltime DESC, seriesName DESC, dbid);''' )
			]


			for name, table, nameFormat in indexes:
				if not name.lower() in haveIndexes:
					cur.execute(nameFormat % (name, table))



		self.conn.commit()
		self.log.info("Retreived page database created")

	@abc.abstractmethod
	def go(self):
		pass

