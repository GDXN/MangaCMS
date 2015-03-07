

import logging
import psycopg2
import threading
import abc
import traceback
import time
import settings
import nameTools as nt
import ScrapePlugins.DbBase

class MonitorBase(ScrapePlugins.DbBase.DbBase):

	# Abstract class (must be subclassed)
	__metaclass__ = abc.ABCMeta

	loggers = {}
	dbConnections = {}
	lastLoggerIndex = 1

	@abc.abstractmethod
	def pluginName(self):
		return None

	@abc.abstractmethod
	def loggerPath(self):
		return None

	@abc.abstractmethod
	def tableName(self):
		return None

	# @abc.abstractmethod
	# def nameMapTableName(self):
	# 	return None

	seriesMonitor = False

	'''
	Source items:
	seriesEntry - Is this the entry for a series, or a individual volume/chapter
	cTitle      - Chapter Title (cleaned for URL use)
	oTitle      - Chapter Title (Raw, can contain non-URL safe chars)
	jTitle      - Title in Japanese
	vTitle      - Volume Title
	jvTitle     - Japanese Volume Title
	series      - Light Novel
	pub	        - Publisher
	label       - Light Novel Label
	volNo       - Volumes
	author      - Author
	illust      - Illustrator
	target      - Target Readership
	relDate     - Release Date
	covers      - Cover Array
	'''



	def __init__(self):
		self.loggers = {}
		self.dbConnections = {}
		self.lastLoggerIndex = 1


		self.log = logging.getLogger(self.loggerPath)
		self.log.info("Loading %s Monitor BaseClass", self.pluginName)
		self.openDB()
		self.checkInitPrimaryDb()

		self.validKwargs  = [
							"changeState",

							"cTitle",
							"oTitle",
							"jTitle",
							"vTitle",
							"jvTitle",
							"series",
							"pub",
							"label",
							"volNo",
							"author",
							"illust",
							"target",
							"relDate",
							"covers",
							"description",

							"seriesEntry",

							"lastChanged",
							"lastChecked",
							"firstSeen"]

		self.validColName = [
							"dbId",
							"changeState",

							"cTitle",
							"oTitle",
							"vTitle",
							"jTitle",
							"jvTitle",
							"series",
							"pub",
							"label",
							"volNo",
							"author",
							"illust",
							"target",
							"relDate",
							"covers",
							"description",

							"seriesEntry",

							"lastChanged",
							"lastChecked",
							"firstSeen"]



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


	# ---------------------------------------------------------------------------------------------------------------------------------------------------------
	# DB Tools
	# ---------------------------------------------------------------------------------------------------------------------------------------------------------
	# Operations are MASSIVELY faster if you set commit=False (it doesn't flush the write to disk), but that can open a transaction which locks the DB.
	# Only pass commit=False if the calling code can gaurantee it'll call commit() itself within a reasonable timeframe.


	def buildInsertArgs(self, **kwargs):

		keys = []
		values = []
		queryAdditionalArgs = []
		for key in kwargs.keys():
			if key not in self.validKwargs:
				raise ValueError("Invalid keyword argument: %s" % key)
			keys.append("{key}".format(key=key))
			values.append("%s")
			queryAdditionalArgs.append("{s}".format(s=kwargs[key]))

		keysStr = ",".join(keys)
		valuesStr = ",".join(values)

		return keysStr, valuesStr, queryAdditionalArgs


	# Insert new item into DB.
	# MASSIVELY faster if you set commit=False (it doesn't flush the write to disk), but that can open a transaction which locks the DB.
	# Only pass commit=False if the calling code can gaurantee it'll call commit() itself within a reasonable timeframe.
	def insertIntoDb(self, commit=True, **kwargs):
		keysStr, valuesStr, queryAdditionalArgs = self.buildInsertArgs(**kwargs)

		query = '''INSERT INTO {tableName} ({keys}) VALUES ({values});'''.format(tableName=self.tableName, keys=keysStr, values=valuesStr)

		# print("Query = ", query, queryAdditionalArgs)


		with self.transaction(commit=commit) as cur:
			cur.execute(query, queryAdditionalArgs)

		if commit:
			self.conn.commit()


	# Update entry with key sourceUrl with values **kwargs
	# kwarg names are checked for validity, and to prevent possiblity of sql injection.
	def updateDbEntry(self, dbId, commit=True, **kwargs):
		print("FIXME?")
		# traceback.print_stack()
		# # lowercase the tags/genre
		# if "srcGenre" in kwargs:
		# 	kwargs['srcGenre'] = kwargs['srcGenre'].lower()
		# if "srcTags" in kwargs:
		# 	kwargs['srcTags'] = kwargs['srcTags'].lower()

		queries = []
		qArgs = []

		row = self.getRowByValue(dbId=dbId)
		if not row:
			raise ValueError("Trying to update a row that doesn't exist!")

		if len(kwargs) == 0:
			raise ValueError("You must pass something to update!")
		for key in kwargs.keys():
			if key not in self.validKwargs:
				raise ValueError("Invalid keyword argument: %s" % key)
			else:
				queries.append("{k}=%s".format(k=key))
				qArgs.append(kwargs[key])

		qArgs.append(dbId)
		column = ", ".join(queries)


		query = '''UPDATE {t} SET {v} WHERE dbId=%s;'''.format(t=self.tableName, v=column)

		with self.transaction(commit=commit) as cur:

			cur.execute(query, qArgs)




	def deleteRowById(self, rowId, commit=True):
		query = ''' DELETE FROM {tableN} WHERE dbId=%s;'''.format(tableN=self.tableName)
		qArgs = (rowId, )

		with self.transaction(commit=commit) as cur:
			cur.execute(query, qArgs)


	# def deleteRowBySrc(self, srcId, commit=True):
	# 	srcId = str(srcId)
	# 	query1 = ''' DELETE FROM {tableN} WHERE srcId=%s;'''.format(tableN=self.nameMapTableName)
	# 	qArgs = (srcId, )
	# 	query2 = ''' DELETE FROM {tableN} WHERE srcId=%s;'''.format(tableN=self.tableName)
	# 	qArgs = (srcId, )

	# 	with self.transaction(commit=commit) as cur:
	# 		cur.execute(query1, qArgs)
	# 		cur.execute(query2, qArgs)

	# 	if commit:
	# 		self.conn.commit()

	def getRowsByValue(self, **kwargs):
		if len(kwargs) != 1:
			raise ValueError("getRowsByValue only supports calling with a single kwarg", kwargs)
		validCols = ["dbId", "cTitle", "changeState"]
		key, val = kwargs.popitem()
		if key not in validCols:
			raise ValueError("Invalid column query: %s" % key)


		# # work around the auto-cast of numeric strings to integers
		typeSpecifier = ''
		# if key == "srcId":
		# 	typeSpecifier = '::TEXT'


		query = '''SELECT {cols} FROM {tableN} WHERE {key}=%s{type};'''.format(cols=", ".join(self.validColName), tableN=self.tableName, key=key, type=typeSpecifier)
		# print("Query = ", query)

		with self.conn.cursor() as cur:
			cur.execute(query, (val, ))
			rets = cur.fetchall()

		retL = []
		if rets:
			keys = self.validColName
			for ret in rets:
				retL.append(dict(zip(keys, ret)))
		return retL

	def getRowByValue(self, **kwargs):
		rows = self.getRowsByValue(**kwargs)
		if len(rows) == 1:
			return rows.pop()
		if len(rows) == 0:
			return None
		else:
			raise ValueError("Got multiple rows for selection. Wat?")



	def getColumnItems(self, colName):
		if not colName in self.validColName:
			raise ValueError("getColumn must be called with a valid column name", colName)

		query = ''' SELECT ({colName}) FROM {tableN};'''.format(colName=colName, tableN=self.tableName)

		with self.conn.cursor() as cur:
			cur.execute(query)
			rets = cur.fetchall()

		retL = []
		if rets:
			for item in rets:
				retL.append(item[0])
		return retL


	# ---------------------------------------------------------------------------------------------------------------------------------------------------------
	# DB Management
	# ---------------------------------------------------------------------------------------------------------------------------------------------------------




	def checkInitPrimaryDb(self):

		self.log.info( "Content Retreiver Opening DB...",)
		with self.conn.cursor() as cur:
			## LastChanged is when the last scanlation release was released
			# Last checked is when the page was actually last scanned.
			cur.execute('''CREATE TABLE IF NOT EXISTS {tableName} (
												dbId            SERIAL PRIMARY KEY,

												changeState      int DEFAULT 0,

												cTitle           CITEXT UNIQUE,
												oTitle           text,
												vTitle           text,
												jTitle           text,
												jvTitle          text,
												series           text,
												pub              text,
												label            text,
												volNo            CITEXT,
												author           text,
												illust           text,
												target           CITEXT,
												description      text,

												seriesEntry      BOOL,

												covers           text[],


												relDate         double precision,
												lastChanged     double precision,
												lastChecked     double precision,
												firstSeen       double precision NOT NULL,

												constraint {tableName}_uniqueSeries unique (cTitle, seriesEntry)
												);'''.format(tableName=self.tableName))

			cur.execute("SELECT relname FROM pg_class;")
			haveIndexes = cur.fetchall()
			haveIndexes = [index[0] for index in haveIndexes]

			indexes = [	("%s_lastChanged_index"  % self.tableName, self.tableName, '''CREATE INDEX %s ON %s (lastChanged)'''),
						("%s_changeState_index"  % self.tableName, self.tableName, '''CREATE INDEX %s ON %s (changeState)'''),
						("%s_lastChecked_index"  % self.tableName, self.tableName, '''CREATE INDEX %s ON %s (lastChecked)'''),
						("%s_firstSeen_index"    % self.tableName, self.tableName, '''CREATE INDEX %s ON %s (firstSeen)'''  ),

						("%s_cTitle_index"       % self.tableName, self.tableName, '''CREATE INDEX %s ON %s (cTitle)'''     ),
						("%s_target_index"       % self.tableName, self.tableName, '''CREATE INDEX %s ON %s (target)'''     ),
						("%s_series_index"       % self.tableName, self.tableName, '''CREATE INDEX %s ON %s (series)'''     ),
						("%s_seriesEntry_index"  % self.tableName, self.tableName, '''CREATE INDEX %s ON %s (seriesEntry)'''),

						# # And the GiN indexes to allow full-text searching so we can search by genre/tags.
						# ("%s_srcTags_gin_index"   % self.tableName, self.tableName, '''CREATE INDEX %s ON %s USING gin((lower(srcTags)::tsvector))'''),
						# ("%s_srcGenre_gin_index"  % self.tableName, self.tableName, '''CREATE INDEX %s ON %s USING gin((lower(srcGenre)::tsvector))'''),

			]
			for name, table, nameFormat in indexes:
				if not name.lower() in haveIndexes:
					cur.execute(nameFormat % (name, table))


			# CREATE INDEX mangaseries_srcTags_gist_index ON mangaseries USING gist(to_tsvector('simple', srcTags));
			# CREATE INDEX mangaseries_srcGenre_gist_index ON mangaseries USING gist(to_tsvector('simple', srcGenre));

			# CREATE INDEX mangaseries_srcTags_gin_index ON mangaseries USING gin(to_tsvector('simple', srcTags));
			# CREATE INDEX mangaseries_srcGenre_gin_index ON mangaseries USING gin(to_tsvector('simple', srcGenre));

			# SELECT * FROM ts_stat('SELECT to_tsvector(''english'',srcTags) from mangaseries') ORDER BY nentry DESC;

			# DROP INDEX mangaseries_srcGenre_gin_index;
			# DROP INDEX mangaseries_srcTags_gin_index;

			# CREATE INDEX mangaseries_srcGenre_gin_index ON mangaseries USING gin((lower(srcGenre)::tsvector));
			# CREATE INDEX mangaseries_srcTags_gin_index ON mangaseries USING gin((lower(srcTags)::tsvector));


			# cur.execute('''CREATE TABLE IF NOT EXISTS %s (
			# 									dbId            SERIAL PRIMARY KEY,
			# 									srcId            text,
			# 									name            CITEXT,
			# 									fsSafeName      CITEXT,
			# 									FOREIGN KEY(srcId) REFERENCES %s(srcId),
			# 									UNIQUE(srcId, name)
			# 									);''' % (self.nameMapTableName, self.tableName))



			# indexes = [	("%s_nameTable_srcId_index"      % self.nameMapTableName, self.nameMapTableName, '''CREATE INDEX %s ON %s (srcId      )'''       ),
			# 			("%s_nameTable_name_index"      % self.nameMapTableName, self.nameMapTableName, '''CREATE INDEX %s ON %s (name      )'''       ),
			# 			("%s_fSafeName_fs_name_index"      % self.nameMapTableName, self.nameMapTableName, '''CREATE INDEX %s ON %s (fsSafeName, name)''' ),
			# 			("%s_fSafeName_name_index"      % self.nameMapTableName, self.nameMapTableName, '''CREATE INDEX %s ON %s (fsSafeName)'''       )
			# ]

			# for name, table, nameFormat in indexes:
			# 	if not name.lower() in haveIndexes:
			# 		print(name, table, nameFormat)
			# 		cur.execute(nameFormat % (name, table))


		self.conn.commit()
		self.log.info("Retreived page database created")

	@abc.abstractmethod
	def go(self):
		pass
