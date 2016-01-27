

import logging
import psycopg2
import threading
import abc
import traceback
import time
import settings
import nameTools as nt
import ScrapePlugins.DbBase

class MonitorDbBase(ScrapePlugins.DbBase.DbBase):
	'''
	This was originally supposed to be a general purpose series monitoring
	base, but at this point it's basically only useful for MangaUpdates.
	Meh?
	'''

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
	def dbName(self):
		return None

	@abc.abstractmethod
	def tableName(self):
		return None

	@abc.abstractmethod
	def nameMapTableName(self):
		return None





	def __init__(self):
		self.loggers = {}
		self.dbConnections = {}
		self.lastLoggerIndex = 1


		self.log = logging.getLogger(self.loggerPath)
		self.log.info("Loading %s Monitor BaseClass", self.pluginName)
		self.openDB()
		self.checkInitPrimaryDb()

		self.validKwargs  = ["buName",
							"buId",
							"buTags",
							"buGenre",
							"buList",

							"buArtist",
							"buAuthor",
							"buOriginState",
							"buDescription",
							"buRelState",
							"buType",

							"readingProgress",
							"availProgress",
							"rating",
							"lastChanged",
							"lastChecked",
							"itemAdded"]

		self.validColName = ["dbId",
							"buName",
							"buId",
							"buTags",
							"buGenre",
							"buList",

							"buArtist",
							"buAuthor",
							"buOriginState",
							"buDescription",
							"buRelState",
							"buType",

							"readingProgress",
							"availProgress",
							"rating",
							"lastChanged",
							"lastChecked",
							"itemAdded"]



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

		# lowercase the tags/genre
		if "buGenre" in kwargs:
			kwargs['buGenre'] = kwargs['buGenre'].lower()
		if "buTags" in kwargs:
			kwargs['buTags'] = kwargs['buTags'].lower()

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

		try:
			with self.transaction(commit=commit) as cur:
				cur.execute(query, qArgs)
		except Exception as e:
			print(query)
			print(qArgs)
			raise e



	def deleteRowById(self, rowId, commit=True):
		query = ''' DELETE FROM {tableN} WHERE dbId=%s;'''.format(tableN=self.tableName)
		qArgs = (rowId, )

		with self.transaction(commit=commit) as cur:

			cur.execute(query, qArgs)


	def deleteRowByBuId(self, buId, commit=True):
		buId = str(buId)
		query1 = ''' DELETE FROM {tableN} WHERE buId=%s;'''.format(tableN=self.nameMapTableName)
		qArgs = (buId, )
		query2 = ''' DELETE FROM {tableN} WHERE buId=%s;'''.format(tableN=self.tableName)
		qArgs = (buId, )


		with self.transaction(commit=commit) as cur:

			cur.execute(query1, qArgs)
			cur.execute(query2, qArgs)

		if commit:
			self.conn.commit()

	def getRowsByValue(self, **kwargs):
		if len(kwargs) != 1:
			raise ValueError("getRowsByValue only supports calling with a single kwarg", kwargs)
		validCols = ["dbId", "buName", "buId"]
		key, val = kwargs.popitem()
		if key not in validCols:
			raise ValueError("Invalid column query: %s" % key)


		# work around the auto-cast of numeric strings to integers
		typeSpecifier = ''
		if key == "buId":
			typeSpecifier = '::TEXT'


		query = '''SELECT {cols} FROM {tableN} WHERE {key}=%s{type};'''.format(cols=", ".join(self.validColName), tableN=self.tableName, key=key, type=typeSpecifier)
		# print("Query = ", query)

		with self.transaction() as cur:
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
			ret = cur.execute(query)
			rets = cur.fetchall()

		retL = []
		if rets:
			for item in rets:
				retL.append(item[0])
		return retL

	def mergeItems(self, fromDict, toDict):
		validMergeKeys = ["dbId", "buName", "buId"]
		for modeDict in [fromDict, toDict]:
			if len(modeDict) != 1:
				raise ValueError("Each selector item must only be a single item long!")
			for key in modeDict.keys():
				if key not in modeDict:
					raise ValueError("Invalid column name {name}. Column name must be one of {validNames}!".format(name=key, validNames=validMergeKeys))

		# At this point, we know we have theoretically valid DB keys. Now, to check the actual values are even valid.


		fromRow = self.getRowByValue(**fromDict)
		toRow   = self.getRowByValue(**toDict)

		if not fromRow:
			raise ValueError("FromRow has no corresponding value in the dictionary! FromRow={row1}".format(row1=fromRow))
		if not toRow:
			raise ValueError("ToRow has no corresponding value in the dictionary! ToRow={row2}".format(row2=toRow))

		# self.printDict(fromRow)
		# self.printDict(toRow)
		if fromRow['dbId'] == toRow['dbId']:
			raise ValueError("Trying to merge row with itself? Error.")

		noCopyKeys = ["dbId"]
		takeLarger = ["rating", "lastChanged"]
		for key in fromRow.keys():
			if key in noCopyKeys:
				continue


			elif key in takeLarger:
				if toRow[key] and fromRow[key]:
					if fromRow[key] > toRow[key]:
						toRow[key] = fromRow[key]
				elif fromRow[key]:
					toRow[key] = fromRow[key]
			else:
				if fromRow[key] != None:
					toRow[key] = fromRow[key]

		# self.printDict(toRow)
		try:
			dbId = toRow["dbId"]
			toRow.pop("dbId")


			with self.transaction():

				self.deleteRowById(fromRow["dbId"], commit=False)
				self.updateDbEntry(dbId, commit=False, **toRow)

		except (psycopg2.OperationalError, psycopg2.IntegrityError) as e:
			self.log.critical("Encountered error!")
			self.log.critical(e)
			traceback.print_exc()
			self.conn.rollback()
			self.log.critical("Rolled back")
			raise e

	def printDict(self, inDict):
		keys = list(inDict.keys())
		keys.sort()
		print("Dict ------")
		for key in keys:
			keyStr = "{key}".format(key=key)
			print("	", keyStr, " "*(20-len(keyStr)), inDict[key])

	def printDb(self):
		with self.conn.cursor() as cur:
			cur.execute('SELECT * FROM {db};'.format(db=self.tableName))
			for line in cur.fetchall():
				print(line)


	def insertBareNameItems(self, items):

		new = 0
		with self.transaction() as cur:


			for name, mId in items:
				row = self.getRowByValue(buId=mId)
				if row:
					if name.lower() != row["buName"].lower():
						self.log.warning("Name disconnect!")
						self.log.warning("New name='%s', old name='%s'.", name, row["buName"])
						self.log.warning("Whole row=%s", row)
						self.updateDbEntry(row["dbId"], buName=name, commit=False, lastChanged=0, lastChecked=0)

				else:
					row = self.getRowByValue(buName=name)
					if row:
						self.log.error("Conflicting with existing series?")
						self.log.error("Existing row = %s, %s", row["buName"], row["buId"])
						self.log.error("Current item = %s, %s", name, mId)
						self.updateDbEntry(row["dbId"], buName=name, commit=False, lastChanged=0, lastChecked=0)
					else:
						self.insertIntoDb(buName=name,
										buId=mId,
										lastChanged=0,
										lastChecked=0,
										itemAdded=time.time(),
										commit=False)
						new += 1
					# cur.execute("""INSERT INTO %s (buId, name)VALUES (?, ?);""" % self.nameMapTableName, (buId, name))

		if new:
			self.log.info("%s new items in inserted set.", new)

	def insertNames(self, buId, names):
		self.log.info("Updating name synonym table for %s with %s name(s).", buId, len(names))
		with self.transaction() as cur:


			# delete the old names from the table, so if they're removed from the source, we'll match that.
			cur.execute("DELETE FROM {tableName} WHERE buId=%s;".format(tableName=self.nameMapTableName), (buId, ))

			alreadyAddedNames = []
			for name in names:
				fsSafeName = nt.prepFilenameForMatching(name)
				if not fsSafeName:
					fsSafeName = nt.makeFilenameSafe(name)

				# we have to block duplicate names. Generally, it's pretty common
				# for multiple names to screen down to the same name after
				# passing through `prepFilenameForMatching()`.
				if fsSafeName in alreadyAddedNames:
					continue

				alreadyAddedNames.append(fsSafeName)

				cur.execute("""INSERT INTO %s (buId, name, fsSafeName) VALUES (%%s, %%s, %%s);""" % self.nameMapTableName, (buId, name, fsSafeName))

		self.log.info("Updated!")
	def getIdFromName(self, name):

		with self.conn.cursor() as cur:
			cur.execute("""SELECT buId FROM %s WHERE name=%%s;""" % self.nameMapTableName, (name, ))
			ret = cur.fetchall()
		if ret:
			if len(ret[0]) != 1:
				raise ValueError("Have ambiguous name. Cannot definitively link to manga series.")
			return ret[0][0]
		else:
			return None

	def getIdFromDirName(self, fsSafeName):

		with self.conn.cursor() as cur:
			cur.execute("""SELECT buId FROM %s WHERE fsSafeName=%%s;""" % self.nameMapTableName, (fsSafeName, ))
			ret = cur.fetchall()
		if ret:
			if len(ret[0]) != 1:
				raise ValueError("Have ambiguous fsSafeName. Cannot definitively link to manga series.")
			return ret[0][0]
		else:
			return None

	def getNamesFromId(self, mId):

		with self.conn.cursor() as cur:
			cur.execute("""SELECT name FROM %s WHERE buId=%%s::TEXT;""" % self.nameMapTableName, (mId, ))
			ret = cur.fetchall()
		if ret:
			return ret
		else:
			return None


	def getLastCheckedFromId(self, mId):

		with self.conn.cursor() as cur:
			ret = cur.execute("""SELECT lastChecked FROM %s WHERE buId=%%s::TEXT;""" % self.tableName, (mId, ))
			ret = cur.fetchall()
		if len(ret) > 1:
			raise ValueError("How did you get more then one buId?")
		if ret:
			# Return structure is [(time)]
			# we want to just return time
			return ret[0][0]
		else:
			return 0


	def updateLastCheckedFromId(self, mId, changed):
		with self.conn.cursor() as cur:
			cur.execute("""UPDATE %s SET lastChecked=%%s WHERE buId=%%s::TEXT;""" % self.tableName, (changed, mId))
		self.conn.commit()




	# ---------------------------------------------------------------------------------------------------------------------------------------------------------
	# DB Management
	# ---------------------------------------------------------------------------------------------------------------------------------------------------------


	def checkInitPrimaryDb(self):

		self.log.info( "Content Retreiver Opening DB...",)
		with self.conn.cursor() as cur:
			## LastChanged is when the last scanlation release was released
			# Last checked is when the page was actually last scanned.
			cur.execute('''CREATE TABLE IF NOT EXISTS %s (
												dbId            SERIAL PRIMARY KEY,

												buName          CITEXT,
												buId            text UNIQUE,
												buTags          CITEXT,
												buGenre         CITEXT,
												buList          CITEXT,

												buArtist        text,
												buAuthor        text,
												buOriginState   text,
												buDescription   text,
												buRelState      text,
												buType          text,

												readingProgress int,
												availProgress   int,

												rating          int,
												lastChanged     double precision,
												lastChecked     double precision,
												itemAdded       double precision NOT NULL
												);''' % self.tableName)

			cur.execute("SELECT relname FROM pg_class;")
			haveIndexes = cur.fetchall()
			haveIndexes = [index[0] for index in haveIndexes]




			indexes = [	("%s_lastChanged_index"  % self.tableName, self.tableName, '''CREATE INDEX %s ON %s (lastChanged)'''),
						("%s_lastChecked_index"  % self.tableName, self.tableName, '''CREATE INDEX %s ON %s (lastChecked)'''),
						("%s_itemAdded_index"    % self.tableName, self.tableName, '''CREATE INDEX %s ON %s (itemAdded)'''  ),
						("%s_rating_index"       % self.tableName, self.tableName, '''CREATE INDEX %s ON %s (rating)'''     ),
						("%s_buName_index"       % self.tableName, self.tableName, '''CREATE INDEX %s ON %s (buName)''' ),
						("%s_buId_index"         % self.tableName, self.tableName, '''CREATE INDEX %s ON %s (buId  )''' ),
						("%s_buTags_index"       % self.tableName, self.tableName, '''CREATE INDEX %s ON %s (buTags)''' ),
						("%s_buGenre_index"      % self.tableName, self.tableName, '''CREATE INDEX %s ON %s (buGenre)'''),
						("%s_buType_index"       % self.tableName, self.tableName, '''CREATE INDEX %s ON %s (buType)'''),

						# And the GiN indexes to allow full-text searching so we can search by genre/tags.
						("%s_buTags_gin_index"   % self.tableName, self.tableName, '''CREATE INDEX %s ON %s USING gin((lower(buTags)::tsvector))'''),
						("%s_buGenre_gin_index"  % self.tableName, self.tableName, '''CREATE INDEX %s ON %s USING gin((lower(buGenre)::tsvector))'''),

			]
			for name, table, nameFormat in indexes:
				if not name.lower() in haveIndexes:
					cur.execute(nameFormat % (name, table))


			# CREATE INDEX mangaseries_buTags_gist_index ON mangaseries USING gist(to_tsvector('simple', buTags));
			# CREATE INDEX mangaseries_buGenre_gist_index ON mangaseries USING gist(to_tsvector('simple', buGenre));

			# CREATE INDEX mangaseries_buTags_gin_index ON mangaseries USING gin(to_tsvector('simple', buTags));
			# CREATE INDEX mangaseries_buGenre_gin_index ON mangaseries USING gin(to_tsvector('simple', buGenre));

			# SELECT * FROM ts_stat('SELECT to_tsvector(''english'',buTags) from mangaseries') ORDER BY nentry DESC;

			# DROP INDEX mangaseries_buGenre_gin_index;
			# DROP INDEX mangaseries_buTags_gin_index;

			# CREATE INDEX mangaseries_buGenre_gin_index ON mangaseries USING gin((lower(buGenre)::tsvector));
			# CREATE INDEX mangaseries_buTags_gin_index ON mangaseries USING gin((lower(buTags)::tsvector));


			cur.execute('''CREATE TABLE IF NOT EXISTS %s (
												dbId            SERIAL PRIMARY KEY,
												buId            text,
												name            CITEXT,
												fsSafeName      CITEXT,
												FOREIGN KEY(buId) REFERENCES %s(buId),
												UNIQUE(buId, name)
												);''' % (self.nameMapTableName, self.tableName))



			indexes = [	("%s_nameTable_buId_index"      % self.nameMapTableName, self.nameMapTableName, '''CREATE INDEX %s ON %s (buId      )'''       ),
						("%s_nameTable_name_index"      % self.nameMapTableName, self.nameMapTableName, '''CREATE INDEX %s ON %s (name      )'''       ),
						("%s_fSafeName_fs_name_index"   % self.nameMapTableName, self.nameMapTableName, '''CREATE INDEX %s ON %s (fsSafeName, name)''' ),
						("%s_fSafeName_name_index"      % self.nameMapTableName, self.nameMapTableName, '''CREATE INDEX %s ON %s (fsSafeName)'''       )
			]


			cur.execute('''CREATE TABLE IF NOT EXISTS %s (
												dbId            SERIAL PRIMARY KEY,
												buId            text,
												vol             double precision,
												chap            double precision,
												other           text,
												releaseText     text,

												FOREIGN KEY(buId) REFERENCES %s(buId),
												UNIQUE(buId, vol, chap, other)
												);''' % (self.itemReleases, self.tableName))



			indexes = [
						("%s_nameTable_buId_index"      % self.itemReleases, self.itemReleases, '''CREATE INDEX %s ON %s (buId      )'''       ),

			]

			for name, table, nameFormat in indexes:
				if not name.lower() in haveIndexes:
					print(name, table, nameFormat)
					cur.execute(nameFormat % (name, table))


		self.conn.commit()
		self.log.info("Retreived page database created")

	@abc.abstractmethod
	def go(self):
		pass
