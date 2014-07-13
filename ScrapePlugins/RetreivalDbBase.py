

import logging
import sqlite3
import abc

import threading
import settings
import os
import traceback

import nameTools as nt

class ScraperDbBase(metaclass=abc.ABCMeta):

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







	# ---------------------------------------------------------------------------------------------------------------------------------------------------------
	# Messy hack to do log indirection so I can inject thread info into log statements, and give each thread it's own DB handle.
	# Basically, intercept all class member accesses, and if the access is to either the logging interface, or the DB,
	# look up/create a per-thread instance of each, and return that
	#
	# The end result is each thread just uses `self.conn` and `self.log` as normal, but actually get a instance of each that is
	# specifically allocated for just that thread
	#
	# Sqlite3 doesn't like having it's DB handles shared across threads. You can turn the checking off, but I had
	# db issues when it was disabled. This is a much more robust fix
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
				self.dbConnections[threadName] = sqlite3.connect(self.dbName, timeout=10)
				rets = self.dbConnections[threadName].execute('''PRAGMA journal_mode=wal;''')
				rets = rets.fetchall()
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


	def openDB(self):
		pass
		# self.log.info("Opening DB...",)
		# self.conn = sqlite3.connect(self.dbName, timeout=10)

		# self.log.info("DB opened. Activating 'wal' mode, exclusive locking")
		# rets = self.conn.execute('''PRAGMA journal_mode=wal;''')
		# # rets = self.conn.execute('''PRAGMA locking_mode=EXCLUSIVE;''')
		# rets = rets.fetchall()

		# self.log.info("PRAGMA return value = %s", rets)

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
			self.log.info( "Have target dir for '%s' Dir = '%s'", canonSeriesName, nt.dirNameProxy[canonSeriesName]['fqPath'])
			return nt.dirNameProxy[canonSeriesName]["fqPath"], False
		else:
			self.log.info( "Don't have target dir for: %s, full name = %s", canonSeriesName, seriesName)
			targetDir = os.path.join(settings.skSettings["dirs"]['mDlDir'], safeBaseName)
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
		values = ["?"]
		queryArguments = [self.tableKey]

		for key in kwargs.keys():
			if key not in self.validKwargs:
				raise ValueError("Invalid keyword argument: %s" % key)
			keys.append("{key}".format(key=key))
			values.append("?")
			queryArguments.append("{s}".format(s=kwargs[key]))

		keysStr = ",".join(keys)
		valuesStr = ",".join(values)

		return keysStr, valuesStr, queryArguments


	# Insert new item into DB.
	# MASSIVELY faster if you set commit=False (it doesn't flush the write to disk), but that can open a transaction which locks the DB.
	# Only pass commit=False if the calling code can gaurantee it'll call commit() itself within a reasonable timeframe.
	def insertIntoDb(self, commit=True, **kwargs):


		cur = self.conn.cursor()
		keysStr, valuesStr, queryArguments = self.buildInsertArgs(**kwargs)

		query = '''INSERT INTO AllMangaItems ({keys}) VALUES ({values});'''.format(keys=keysStr, values=valuesStr)

		# print("Query = ", query, queryArguments)

		cur.execute(query, queryArguments)

		if commit:
			self.conn.commit()


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
				queries.append("{k}=?".format(k=key))
				qArgs.append(kwargs[key])

		qArgs.append(sourceUrl)
		qArgs.append(self.tableKey)
		column = ", ".join(queries)

		cur = self.conn.cursor()

		query = '''UPDATE AllMangaItems SET {v} WHERE sourceUrl=? AND sourceSite=?;'''.format(v=column)
		cur.execute(query, qArgs)

		if commit:
			self.conn.commit()
		# print("Updating", self.getRowByValue(sourceUrl=sourceUrl))


	def deleteRowsByValue(self, commit=True, **kwargs):
		if len(kwargs) != 1:
			raise ValueError("getRowsByValue only supports calling with a single kwarg", kwargs)
		validCols = ["dbId", "sourceUrl", "dlState"]
		key, val = kwargs.popitem()
		if key not in validCols:
			raise ValueError("Invalid column query: %s" % key)

		cur = self.conn.cursor()

		query = '''DELETE FROM AllMangaItems WHERE {key}=? AND sourceSite=?;'''.format(key=key)
		# print("Query = ", query)
		cur.execute(query, (val, self.tableKey))
		if commit:
			self.conn.commit()




	def getRowsByValue(self, **kwargs):
		if len(kwargs) != 1:
			raise ValueError("getRowsByValue only supports calling with a single kwarg" % kwargs)
		validCols = ["dbId", "sourceUrl", "dlState"]
		key, val = kwargs.popitem()
		if key not in validCols:
			raise ValueError("Invalid column query: %s" % key)

		cur = self.conn.cursor()

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
							FROM AllMangaItems WHERE {key}=? AND sourceSite=?;'''.format(key=key)
		# print("Query = ", query)
		ret = cur.execute(query, (val, self.tableKey))

		rets = ret.fetchall()
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
			existingTags = set(row["tags"])
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
		self.conn.execute('''UPDATE AllMangaItems SET dlState=0 WHERE dlState=1 AND sourceSite=?''', (self.tableKey, ))
		self.conn.commit()
		self.log.info("Download reset complete")


	# ---------------------------------------------------------------------------------------------------------------------------------------------------------
	# DB Management
	# ---------------------------------------------------------------------------------------------------------------------------------------------------------

	def checkInitPrimaryDb(self):

		self.conn.execute('''CREATE TABLE IF NOT EXISTS AllMangaItems (
											dbId          INTEGER PRIMARY KEY,
											sourceSite    TEXT NOT NULL,
											dlState       text NOT NULL,
											sourceUrl     text UNIQUE NOT NULL,
											retreivalTime real NOT NULL,
											lastUpdate    real DEFAULT 0,
											sourceId      text,
											seriesName    text,
											fileName      text,
											originName    text,
											downloadPath  text,
											flags         text,
											tags          text,
											note          text);''')

		self.conn.execute('''CREATE INDEX IF NOT EXISTS %s ON AllMangaItems (sourceSite)'''                 % ("AllMangaItems_source_index"))
		self.conn.execute('''CREATE INDEX IF NOT EXISTS %s ON AllMangaItems (retreivalTime)'''              % ("AllMangaItems_time_index"))
		self.conn.execute('''CREATE INDEX IF NOT EXISTS %s ON AllMangaItems (lastUpdate)'''                 % ("AllMangaItems_lastUpdate_index"))
		self.conn.execute('''CREATE INDEX IF NOT EXISTS %s ON AllMangaItems (sourceUrl)'''                  % ("AllMangaItems_url_index"))
		self.conn.execute('''CREATE INDEX IF NOT EXISTS %s ON AllMangaItems (seriesName collate nocase)'''  % ("AllMangaItems_seriesName_index"))
		self.conn.execute('''CREATE INDEX IF NOT EXISTS %s ON AllMangaItems (tags       collate nocase)'''  % ("AllMangaItems_tags_index"))
		self.conn.execute('''CREATE INDEX IF NOT EXISTS %s ON AllMangaItems (flags      collate nocase)'''  % ("AllMangaItems_flags_index"))
		self.conn.execute('''CREATE INDEX IF NOT EXISTS %s ON AllMangaItems (dlState)'''                    % ("AllMangaItems_dlState_index"))

		self.conn.commit()
		self.log.info("Retreived page database created")

	@abc.abstractmethod
	def go(self):
		pass

