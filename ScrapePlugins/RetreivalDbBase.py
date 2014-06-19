

import logging
import sqlite3
import abc

import threading
import logging

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
			raise ValueError("getRowsByValue only supports calling with a single kwarg", kwargs)
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
