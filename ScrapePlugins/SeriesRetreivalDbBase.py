

import logging
import abc


import nameTools as nt


import ScrapePlugins.RetreivalDbBase
# Turn on to print all db queries to STDOUT before running them.
# Intended for debugging DB interactions.
# Excessively verbose otherwise.
QUERY_DEBUG = False

class SeriesScraperDbBase(ScrapePlugins.RetreivalDbBase.ScraperDbBase):



	@abc.abstractmethod
	def seriesTableName(self):
		return None

	def __init__(self):

		super().__init__()
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
			values.append("%s")
			queryArguments.append("{s}".format(s=kwargs[key]))

		keysStr = ",".join(keys)
		valuesStr = ",".join(values)

		return keysStr, valuesStr, queryArguments


	# Insert new item into DB.
	# MASSIVELY faster if you set commit=False (it doesn't flush the write to disk), but that can open a transaction which locks the DB.
	# Only pass commit=False if the calling code can gaurantee it'll call commit() itself within a reasonable timeframe.
	def insertIntoSeriesDb(self, commit=True, **kwargs):


		keysStr, valuesStr, queryArguments = self.buildSeriesInsertArgs(**kwargs)

		query = '''INSERT INTO {tableName} ({keys}) VALUES ({values});'''.format(tableName=self.seriesTableName, keys=keysStr, values=valuesStr)

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
				queries.append("{k}=%s".format(k=key))
				qArgs.append(kwargs[key])

		qArgs.append(seriesId)

		column = ", ".join(queries)


		query = '''UPDATE {tableName} SET {v} WHERE seriesId=%s;'''.format(tableName=self.seriesTableName, v=column)

		if QUERY_DEBUG:
			print("Query = ", query)
			print("Args = ", qArgs)

		with self.conn.cursor() as cur:

			if commit:
				cur.execute("BEGIN;")

			cur.execute(query, qArgs)

			if commit:
				cur.execute("COMMIT;")


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
				queries.append("{k}=%s".format(k=key))
				qArgs.append(kwargs[key])

		qArgs.append(rowId)

		column = ", ".join(queries)


		query = '''UPDATE {tableName} SET {v} WHERE dbId=%s;'''.format(tableName=self.seriesTableName, v=column)

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



	def getSeriesRowsByValue(self, **kwargs):
		if len(kwargs) != 1:
			raise ValueError("getRowsByValue only supports calling with a single kwarg" % kwargs)
		validCols = ["dbId", "seriesId", "seriesName", "dlState"]
		key, val = kwargs.popitem()
		if key not in validCols:
			raise ValueError("Invalid column query: %s" % key)


		query = '''SELECT
						dbId,
						seriesId,
						seriesName,
						dlState,
						retreivalTime,
						lastUpdate
						FROM {tableName} WHERE {key}=%s ORDER BY retreivalTime DESC;'''.format(tableName=self.seriesTableName, key=key)
		if QUERY_DEBUG:
			print("Query = ", query)
			print("args = ", (val))

		with self.conn.cursor() as cur:
			cur.execute(query, (val,))
			rets = cur.fetchall()

		retL = []
		for row in rets:

			keys = ["dbId", "seriesId", "seriesName", "dlState", "retreivalTime", "lastUpdate"]
			retL.append(dict(zip(keys, row)))
		return retL



	def resetStuckSeriesItems(self):
		self.log.info("Resetting stuck downloads in DB")
		with self.conn.cursor() as cur:
			cur.execute('''UPDATE {tableName} SET dlState=0 WHERE dlState=1'''.format(tableName=self.seriesTableName))
		self.conn.commit()
		self.log.info("Download reset complete")



	def checkInitSeriesDb(self):

		with self.conn.cursor() as cur:
			cur.execute('''CREATE TABLE IF NOT EXISTS {tableName} (
												dbId          SERIAL PRIMARY KEY,
												seriesId      TEXT NOT NULL,
												seriesName    TEXT NOT NULL,
												dlState       text NOT NULL,
												retreivalTime double precision NOT NULL,
												lastUpdate    double precision DEFAULT 0
												);'''.format(tableName=self.seriesTableName))




			cur.execute("SELECT relname FROM pg_class;")
			haveIndexes = cur.fetchall()
			haveIndexes = [index[0] for index in haveIndexes]



		indexes = [	("%s_serId_index"      % self.seriesTableName, self.seriesTableName,'''CREATE INDEX %s ON %s (seriesId)'''      ),
					("%s_time_index"       % self.seriesTableName, self.seriesTableName,'''CREATE INDEX %s ON %s (retreivalTime)''' ),
					("%s_lastUpdate_index" % self.seriesTableName, self.seriesTableName,'''CREATE INDEX %s ON %s (lastUpdate)'''    ),
					("%s_seriesName_index" % self.seriesTableName, self.seriesTableName,'''CREATE INDEX %s ON %s (seriesName)'''    )
		]

		for name, table, nameFormat in indexes:
			if not name.lower() in haveIndexes:
				cur.execute(nameFormat % (name, table))

		self.conn.commit()
		self.log.info("Retreived page database created")
