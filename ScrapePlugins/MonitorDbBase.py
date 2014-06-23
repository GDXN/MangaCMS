

import logging
import sqlite3
import abc
import traceback
import time

class MonitorDbBase(metaclass=abc.ABCMeta):

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
	def tableName(self):
		return None

	@abc.abstractmethod
	def nameMapTableName(self):
		return None




	def __init__(self):
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

							"readingProgress",
							"availProgress",
							"rating",
							"lastChanged",
							"lastChecked",
							"itemAdded"]

	def openDB(self):
		self.log.info("Opening DB...",)
		self.conn = sqlite3.connect(self.dbName, timeout=10)

		self.log.info("DB opened. Activating 'wal' mode, exclusive locking")
		rets = self.conn.execute('''PRAGMA journal_mode=wal;''')
		# rets = self.conn.execute('''PRAGMA locking_mode=EXCLUSIVE;''')
		rets = rets.fetchall()

		self.log.info("PRAGMA return value = %s", rets)

	def closeDB(self):
		self.log.info("Closing DB...",)
		self.conn.close()
		self.log.info("DB Closed")


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
			values.append("?")
			queryAdditionalArgs.append("{s}".format(s=kwargs[key]))

		keysStr = ",".join(keys)
		valuesStr = ",".join(values)

		return keysStr, valuesStr, queryAdditionalArgs


	# Insert new item into DB.
	# MASSIVELY faster if you set commit=False (it doesn't flush the write to disk), but that can open a transaction which locks the DB.
	# Only pass commit=False if the calling code can gaurantee it'll call commit() itself within a reasonable timeframe.
	def insertIntoDb(self, commit=True, **kwargs):
		cur = self.conn.cursor()
		keysStr, valuesStr, queryAdditionalArgs = self.buildInsertArgs(**kwargs)

		query = '''INSERT INTO {tableName} ({keys}) VALUES ({values});'''.format(tableName=self.tableName, keys=keysStr, values=valuesStr)

		# print("Query = ", query, queryAdditionalArgs)

		cur.execute(query, queryAdditionalArgs)

		if commit:
			self.conn.commit()


	# Update entry with key sourceUrl with values **kwargs
	# kwarg names are checked for validity, and to prevent possiblity of sql injection.
	def updateDbEntry(self, dbId, commit=True, **kwargs):


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
				queries.append("{k}=?".format(k=key))
				qArgs.append(kwargs[key])

		qArgs.append(dbId)
		column = ", ".join(queries)

		cur = self.conn.cursor()

		query = '''UPDATE {t} SET {v} WHERE dbId=?;'''.format(t=self.tableName, v=column)
		cur.execute(query, qArgs)


		if commit:
			self.conn.commit()

	def deleteRowById(self, rowId, commit=True):

		cur = self.conn.cursor()


		query = ''' DELETE FROM {tableN} WHERE dbId=?;'''.format(tableN=self.tableName)
		qArgs = (rowId, )
		cur.execute(query, qArgs)

		if commit:
			self.conn.commit()

	def getRowsByValue(self, **kwargs):
		if len(kwargs) != 1:
			raise ValueError("getRowsByValue only supports calling with a single kwarg", kwargs)
		validCols = ["dbId", "mtName", "mtId", "buName", "buId"]
		key, val = kwargs.popitem()
		if key not in validCols:
			raise ValueError("Invalid column query: %s" % key)

		cur = self.conn.cursor()

		query = '''SELECT {cols} FROM {tableN} WHERE {key}=?;'''.format(cols=", ".join(self.validColName), tableN=self.tableName, key=key)
		# print("Query = ", query)
		ret = cur.execute(query, (val, ))

		rets = ret.fetchall()
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
		cur = self.conn.cursor()
		if not colName in self.validColName:
			raise ValueError("getColumn must be called with a valid column name", colName)

		query = ''' SELECT ({colName}) FROM {tableN};'''.format(colName=colName, tableN=self.tableName)
		ret = cur.execute(query)

		rets = ret.fetchall()
		retL = []
		if rets:
			for item in rets:
				retL.append(item[0])
		return retL

	def mergeItems(self, fromDict, toDict):
		validMergeKeys = ["dbId", "mtName", "mtId", "buName", "buId"]
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
			raise ValueError("FromRow has no corresponding value in the dictionary! FromRow={row1}".format(row1=fromRow, row2=toRow))
		if not toRow:
			raise ValueError("ToRow has no corresponding value in the dictionary! ToRow={row2}".format(row1=fromRow, row2=toRow))

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
			self.conn.commit()
			self.deleteRowById(fromRow["dbId"], commit=False)
			self.updateDbEntry(dbId, commit=False, **toRow)
			self.conn.commit()

		except (sqlite3.OperationalError, sqlite3.IntegrityError) as e:
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
		cur = self.conn.cursor()
		ret = cur.execute('SELECT * FROM {db};'.format(db=self.tableName))
		for line in ret.fetchall():
			print(line)


	def insertBareNameItems(self, items):

		cur = self.conn.cursor()
		for name, mId in items:
			row = self.getRowByValue(buId=mId)
			if row:
				if name.lower() != row["buName"].lower():
					self.log.warning("Name disconnect!")
					self.log.warning("New name='%s', old name='%s'.", name, row["buName"])
					self.log.warning("Whole row=%s", row)
					self.updateDbEntry(row["dbId"], buName=name, commit=False)

			else:
				row = self.getRowByValue(buName=name)
				if row:
					self.log.error("Conflicting with existing series?")
					self.log.error("Existing row = %s, %s", row["buName"], row["buId"])
					self.log.error("Current item = %s, %s", name, mId)
					self.updateDbEntry(row["dbId"], buName=name, commit=False)
				else:
					self.insertIntoDb(buName=name,
									buId=mId,
									lastChanged=0,
									lastChecked=0,
									itemAdded=time.time(),
									commit=False)
				# cur.execute("""INSERT INTO %s (buId, name)VALUES (?, ?);""" % self.nameMapTableName, (buId, name))
		cur.fetchall()
		self.conn.commit()

	def insertNames(self, buId, names):

		cur = self.conn.cursor()
		for name in names:
			cur.execute("""INSERT INTO %s (buId, name)VALUES (?, ?);""" % self.nameMapTableName, (buId, name))
		cur.fetchall()

	def getIdFromName(self, name):

		cur = self.conn.cursor()
		ret = cur.execute("""SELECT buId FROM %s WHERE name=?;""" % self.nameMapTableName, (name, ))
		ret = ret.fetchall()
		if ret:
			if len(ret[0]) != 1:
				raise ValueError("Have ambiguous name. Cannot definitively link to manga series.")
			return ret[0][0]
		else:
			return None

	def getNamesFromId(self, mId):

		cur = self.conn.cursor()
		ret = cur.execute("""SELECT name FROM %s WHERE buId=?;""" % self.nameMapTableName, (mId, ))
		ret = ret.fetchall()
		if ret:
			return ret
		else:
			return None


	# ---------------------------------------------------------------------------------------------------------------------------------------------------------
	# DB Management
	# ---------------------------------------------------------------------------------------------------------------------------------------------------------


	def checkInitPrimaryDb(self):

		self.log.info( "Content Retreiver Opening DB...",)


		self.conn.execute('''CREATE TABLE IF NOT EXISTS %s (
											dbId            INTEGER PRIMARY KEY,

											buName          text COLLATE NOCASE UNIQUE,
											buId            text COLLATE NOCASE UNIQUE,
											buTags          text,
											buGenre         text,
											buList          text,

											buArtist        text,
											buAuthor        text,
											buOriginState   text,
											buDescription   text,
											buRelState      text,

											readingProgress int,
											availProgress   int,

											rating          int,
											lastChanged     real,
											lastChecked     real,
											itemAdded       real NOT NULL
											);''' % self.tableName)

		self.conn.execute('''CREATE INDEX IF NOT EXISTS %s ON %s (lastChanged)'''            % ("%s_lastChanged_index"  % self.tableName, self.tableName))
		self.conn.execute('''CREATE INDEX IF NOT EXISTS %s ON %s (lastChecked)'''            % ("%s_lastChecked_index"  % self.tableName, self.tableName))
		self.conn.execute('''CREATE INDEX IF NOT EXISTS %s ON %s (itemAdded)'''              % ("%s_itemAdded_index"    % self.tableName, self.tableName))
		self.conn.execute('''CREATE INDEX IF NOT EXISTS %s ON %s (rating)'''                 % ("%s_rating_index"       % self.tableName, self.tableName))
		self.conn.execute('''CREATE INDEX IF NOT EXISTS %s ON %s (buName collate nocase)'''  % ("%s_buName_index"       % self.tableName, self.tableName))
		self.conn.execute('''CREATE INDEX IF NOT EXISTS %s ON %s (buId   collate nocase)'''  % ("%s_buId_index"         % self.tableName, self.tableName))
		self.conn.execute('''CREATE INDEX IF NOT EXISTS %s ON %s (buTags collate nocase)'''  % ("%s_buTags_index"       % self.tableName, self.tableName))
		self.conn.execute('''CREATE INDEX IF NOT EXISTS %s ON %s (buGenre collate nocase)''' % ("%s_buGenre_index"      % self.tableName, self.tableName))




		self.conn.execute('''CREATE TABLE IF NOT EXISTS %s (
											dbId            INTEGER PRIMARY KEY,
											buId            text COLLATE NOCASE,
											name            text COLLATE NOCASE,
											FOREIGN KEY(buId) REFERENCES %s(buId),
											UNIQUE(buId, name) ON CONFLICT REPLACE
											);''' % (self.nameMapTableName, self.tableName))

		self.conn.execute('''CREATE INDEX IF NOT EXISTS %s ON %s (buId collate nocase)''' % ("%s_nameTable_mtId_index"      % self.nameMapTableName, self.nameMapTableName))
		self.conn.execute('''CREATE INDEX IF NOT EXISTS %s ON %s (name collate nocase)''' % ("%s_nameTable_name_index"      % self.nameMapTableName, self.nameMapTableName))

		self.conn.commit()
		self.log.info("Retreived page database created")

	@abc.abstractmethod
	def go(self):
		pass
