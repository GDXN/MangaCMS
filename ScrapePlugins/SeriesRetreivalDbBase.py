

import logging
import sqlite3
import abc

import threading
import settings
import os
import traceback

import nameTools as nt


import ScrapePlugins.RetreivalDbBase
# Turn on to print all db queries to STDOUT before running them.
# Intended for debugging DB interactions.
# Excessively verbose otherwise.
QUERY_DEBUG = True

class SeriesScraperDbBase(ScrapePlugins.RetreivalDbBase.ScraperDbBase):



	@abc.abstractmethod
	def seriesTableName(self):
		return None

	def __init__(self):

		self.loggers = {}
		self.dbConnections = {}
		self.lastLoggerIndex = 1

		self.log = logging.getLogger(self.loggerPath)
		self.log.info("Loading %s Runner BaseClass", self.pluginName)
		self.openDB()
		self.checkInitPrimaryDb()
		self.checkInitSeriesDb()




	# ---------------------------------------------------------------------------------------------------------------------------------------------------------
	# DB Management
	# ---------------------------------------------------------------------------------------------------------------------------------------------------------

	validSeriesKwargs = ["seriesId", "seriesName", "dlState", "retreivalTime", "lastUpdate"]

	def buildSeriesInsertArgs(self, **kwargs):

		# Pre-populate with the table keys.
		keys = []
		values = []
		queryArguments = []

		for key in kwargs.keys():
			if key not in self.validSeriesKwargs:
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
	def insertIntoSeriesDb(self, commit=True, **kwargs):


		cur = self.conn.cursor()
		keysStr, valuesStr, queryArguments = self.buildSeriesInsertArgs(**kwargs)

		query = '''INSERT INTO {tableName} ({keys}) VALUES ({values});'''.format(tableName=self.seriesTableName, keys=keysStr, values=valuesStr)

		if QUERY_DEBUG:
			print("Query = ", query)
			print("Args = ", queryArguments)

		cur.execute(query, queryArguments)

		if commit:
			self.conn.commit()



	# Update entry with key sourceUrl with values **kwargs
	# kwarg names are checked for validity, and to prevent possiblity of sql injection.
	def updateSeriesDbEntry(self, seriesId, commit=True, **kwargs):

		# Patch series name.
		if "seriesName" in kwargs and kwargs["seriesName"]:
			kwargs["seriesName"] = nt.getCanonicalMangaUpdatesName(kwargs["seriesName"])


		queries = []
		qArgs = []
		for key in kwargs.keys():
			if key not in self.validSeriesKwargs:
				raise ValueError("Invalid keyword argument: %s" % key)
			else:
				queries.append("{k}=?".format(k=key))
				qArgs.append(kwargs[key])

		qArgs.append(seriesId)

		column = ", ".join(queries)

		cur = self.conn.cursor()

		query = '''UPDATE {tableName} SET {v} WHERE seriesId=?;'''.format(tableName=self.seriesTableName, v=column)

		if QUERY_DEBUG:
			print("Query = ", query)
			print("Args = ", qArgs)

		cur.execute(query, qArgs)

		if commit:
			self.conn.commit()

	# Update entry with key sourceUrl with values **kwargs
	# kwarg names are checked for validity, and to prevent possiblity of sql injection.
	def updateSeriesDbEntryById(self, rowId, commit=True, **kwargs):

		# Patch series name.
		if "seriesName" in kwargs and kwargs["seriesName"]:
			kwargs["seriesName"] = nt.getCanonicalMangaUpdatesName(kwargs["seriesName"])

		queries = []
		qArgs = []
		for key in kwargs.keys():
			if key not in self.validSeriesKwargs:
				raise ValueError("Invalid keyword argument: %s" % key)
			else:
				queries.append("{k}=?".format(k=key))
				qArgs.append(kwargs[key])

		qArgs.append(rowId)

		column = ", ".join(queries)

		cur = self.conn.cursor()

		query = '''UPDATE {tableName} SET {v} WHERE dbId=?;'''.format(tableName=self.seriesTableName, v=column)

		if QUERY_DEBUG:
			print("Query = ", query)
			print("Args = ", qArgs)

		cur.execute(query, qArgs)

		if commit:
			self.conn.commit()
		# print("Updating", self.getRowByValue(sourceUrl=sourceUrl))



	def getSeriesRowsByValue(self, **kwargs):
		if len(kwargs) != 1:
			raise ValueError("getRowsByValue only supports calling with a single kwarg" % kwargs)
		validCols = ["dbId", "seriesId", "seriesName", "dlState"]
		key, val = kwargs.popitem()
		if key not in validCols:
			raise ValueError("Invalid column query: %s" % key)

		cur = self.conn.cursor()

		query = '''SELECT
						dbId,
						seriesId,
						seriesName,
						dlState,
						retreivalTime,
						lastUpdate
						FROM {tableName} WHERE {key}=? ORDER BY retreivalTime DESC;'''.format(tableName=self.seriesTableName, key=key)
		if QUERY_DEBUG:
			print("Query = ", query)
			print("args = ", (val))
		ret = cur.execute(query, (val,))

		rets = ret.fetchall()
		retL = []
		for row in rets:

			keys = ["dbId", "seriesId", "seriesName", "dlState", "retreivalTime", "lastUpdate"]
			retL.append(dict(zip(keys, row)))
		return retL


	def checkInitSeriesDb(self):

		self.conn.execute('''CREATE TABLE IF NOT EXISTS {tableName} (
											dbId          INTEGER PRIMARY KEY,
											seriesId      TEXT NOT NULL,
											seriesName    TEXT NOT NULL,
											dlState       text NOT NULL,
											retreivalTime real NOT NULL,
											lastUpdate    real DEFAULT 0
											);'''.format(tableName=self.seriesTableName))

		self.conn.execute('''CREATE INDEX IF NOT EXISTS %s ON %s (seriesId)'''                         % ("%s_serId_index"      % self.seriesTableName, self.seriesTableName))
		self.conn.execute('''CREATE INDEX IF NOT EXISTS %s ON %s (retreivalTime)'''                    % ("%s_time_index"       % self.seriesTableName, self.seriesTableName))
		self.conn.execute('''CREATE INDEX IF NOT EXISTS %s ON %s (lastUpdate)'''                       % ("%s_lastUpdate_index" % self.seriesTableName, self.seriesTableName))
		self.conn.execute('''CREATE INDEX IF NOT EXISTS %s ON %s (seriesName)'''                       % ("%s_seriesName_index" % self.seriesTableName, self.seriesTableName))


		self.conn.commit()
		self.log.info("Retreived page database created")
