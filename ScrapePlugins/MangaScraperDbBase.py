
if __name__ == "__main__":
	import runStatus
	runStatus.preloadDicts = False

import logging
import psycopg2
import functools
import operator as opclass
import abc

import threading
import settings
import os
import traceback

import nameTools as nt
import DbBase

import sql
import time
import sql.operators as sqlo



class MangaScraperDbBase(DbBase.DbBase):

	# Abstract class (must be subclassed)
	__metaclass__ = abc.ABCMeta

	shouldCanonize = True

	dbConnections = {}

	# Turn on to print all db queries to STDOUT before running them.
	# Intended for debugging DB interactions.
	# Excessively verbose otherwise.
	QUERY_DEBUG = False

	@abc.abstractmethod
	def pluginName(self):
		return None

	@abc.abstractmethod
	def loggerPath(self):
		return None


	@abc.abstractmethod
	def tableKey(self):
		return None

	@abc.abstractmethod
	def tableName(self):
		return None



	validKwargs = ["dlState", "sourceUrl", "retreivalTime", "lastUpdate", "sourceId", "seriesName", "fileName", "originName", "downloadPath", "flags", "tags", "note"]

	def __init__(self):
		super().__init__()

		self.table = sql.Table(self.tableName.lower())

		self.cols = (
				self.table.dbid,
				self.table.dlstate,
				self.table.sourcesite,
				self.table.sourceurl,
				self.table.retreivaltime,
				self.table.lastupdate,
				self.table.sourceid,
				self.table.seriesname,
				self.table.filename,
				self.table.originname,
				self.table.downloadpath,
				self.table.flags,
				self.table.tags,
				self.table.note
			)


		self.colMap = {
				"dbid"          : self.table.dbid,
				"dlstate"       : self.table.dlstate,
				"sourcesite"    : self.table.sourcesite,
				"sourceurl"     : self.table.sourceurl,
				"retreivaltime" : self.table.retreivaltime,
				"lastupdate"    : self.table.lastupdate,
				"sourceid"      : self.table.sourceid,
				"seriesname"    : self.table.seriesname,
				"filename"      : self.table.filename,
				"originname"    : self.table.originname,
				"downloadpath"  : self.table.downloadpath,
				"flags"         : self.table.flags,
				"tags"          : self.table.tags,
				"note"          : self.table.note
			}

		self.log.info("Loading %s Runner BaseClass", self.pluginName)
		self.checkInitPrimaryDb()




	# ---------------------------------------------------------------------------------------------------------------------------------------------------------
	# Misc Utilities
	# ---------------------------------------------------------------------------------------------------------------------------------------------------------

	def _resetStuckItems(self):
		self.log.info("Resetting stuck downloads in DB")
		with self.transaction() as cur:
			cur.execute('''UPDATE {tableName} SET dlState=0 WHERE dlState=1 AND sourceSite=%s'''.format(tableName=self.tableName), (self.tableKey, ))
		self.log.info("Download reset complete")

	# ---------------------------------------------------------------------------------------------------------------------------------------------------------
	# DB Tools
	# ---------------------------------------------------------------------------------------------------------------------------------------------------------

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


	def sqlBuildInsertArgs(self, **kwargs):

		cols = [self.table.sourcesite]
		vals = [self.tableKey]

		for key, val in kwargs.items():
			key = key.lower()

			if key not in self.colMap:
				raise ValueError("Invalid column name for insert! '%s'" % key)
			cols.append(self.colMap[key])
			vals.append(val)

		query = self.table.insert(columns=cols, values=[vals])

		query, params = tuple(query)

		return query, params


	# Insert new item into DB.
	# MASSIVELY faster if you set commit=False (it doesn't flush the write to disk), but that can open a transaction which locks the DB.
	# Only pass commit=False if the calling code can gaurantee it'll call commit() itself within a reasonable timeframe.
	def insertIntoDb(self, commit=True, **kwargs):
		cur = kwargs.pop('cur', None)

		query, queryArguments = self.sqlBuildInsertArgs(**kwargs)

		if self.QUERY_DEBUG:
			print("Query = ", query)
			print("Args = ", queryArguments)
		if cur is not None:
			cur.execute(query, queryArguments)
		else:
			with self.transaction(commit=commit) as cur:
				cur.execute(query, queryArguments)





	def generateUpdateQuery(self, **kwargs):
		if "dbId" in kwargs:
			where = (self.table.dbid == kwargs.pop('dbId'))
		elif "sourceUrl" in kwargs:
			where = (self.table.sourceurl == kwargs.pop('sourceUrl'))
		else:
			raise ValueError("GenerateUpdateQuery must be passed a single unique column identifier (either dbId or sourceUrl)")

		cols = []
		vals = []

		for key, val in kwargs.items():
			key = key.lower()

			if key not in self.colMap:
				raise ValueError("Invalid column name for insert! '%s'" % key)
			cols.append(self.colMap[key])
			vals.append(val)

		query = self.table.update(columns=cols, values=vals, where=where)
		query, params = tuple(query)
		return query, params




	# Update entry with key sourceUrl with values **kwargs
	# kwarg names are checked for validity, and to prevent possiblity of sql injection.
	def updateDbEntry(self, sourceUrl, commit=True, **kwargs):
		cur = kwargs.pop('cur', None)

		# Patch series name.
		if "seriesName" in kwargs and kwargs["seriesName"] and self.shouldCanonize:
			kwargs["seriesName"] = nt.getCanonicalMangaUpdatesName(kwargs["seriesName"])

		# Clamp the retreivaltime to now, so parsing issues that result in invalid, future
		# time-stamps don't cause posts to stick to the top of the post list.
		if 'retreivalTime' in kwargs:
			if kwargs['retreivalTime'] > time.time():
				kwargs['retreivalTime'] = time.time()

		query, queryArguments = self.generateUpdateQuery(sourceUrl=sourceUrl, **kwargs)

		if self.QUERY_DEBUG:
			print("Query = ", query)
			print("Args = ", queryArguments)

		if cur is not None:
			cur.execute(query, queryArguments)
		else:
			with self.transaction(commit=commit) as cur:
				cur.execute(query, queryArguments)


		# print("Updating", self.getRowByValue(sourceUrl=sourceUrl))

	# Update entry with key sourceUrl with values **kwargs
	# kwarg names are checked for validity, and to prevent possiblity of sql injection.
	def updateDbEntryById(self, rowId, commit=True, **kwargs):

		# Patch series name.
		if "seriesName" in kwargs and kwargs["seriesName"] and self.shouldCanonize:
			kwargs["seriesName"] = nt.getCanonicalMangaUpdatesName(kwargs["seriesName"])

		query, queryArguments = self.generateUpdateQuery(dbId=rowId, **kwargs)

		if self.QUERY_DEBUG:
			print("Query = ", query)
			print("Args = ", queryArguments)

		with self.transaction(commit=commit) as cur:
			cur.execute(query, queryArguments)

		# print("Updating", self.getRowByValue(sourceUrl=sourceUrl))



	def deleteRowsByValue(self, commit=True, **kwargs):
		cur = kwargs.pop('cur', None)

		if len(kwargs) != 1:
			raise ValueError("deleteRowsByValue only supports calling with a single kwarg", kwargs)

		validCols = ["dbId", "sourceUrl", "dlState"]

		key, val = kwargs.popitem()
		if key not in validCols:
			raise ValueError("Invalid column query: %s" % key)

		where = (self.colMap[key.lower()] == val)

		query = self.table.delete(where=where)

		query, args = tuple(query)


		if self.QUERY_DEBUG:
			print("Query = ", query)
			print("Args = ", args)

		if cur is not None:
			cur.execute(query, args)
		else:
			with self.transaction(commit=commit) as cur:
				cur.execute(query, args)



	def test(self):
		print("Testing")

		# print(self.sqlBuildInsertArgs(sourcesite='Wat', retreivaltime="lol"))
		# print(self.sqlBuildInsertArgs(sourcesite='Wat', retreivaltime="lol", lastupdate='herp', filename='herp', downloadpath='herp', tags='herp'))

		# print(self.updateDbEntry(sourceUrl='lol', sourcesite='Wat', retreivaltime="lol", lastupdate='herp', filename='herp', downloadpath='herp', tags='herp'))
		# print(self.updateDbEntryById(rowId='lol', sourcesite='Wat', retreivaltime="lol", lastupdate='herp', filename='herp', downloadpath='herp', tags='herp'))
		# print(self.updateDbEntryKey(sourcesite='Wat', retreivaltime="lol", lastupdate='herp', filename='herp', downloadpath='herp', tags='herp'))

		# self.deleteRowsByValue(dbId="lol")
		# self.deleteRowsByValue(sourceUrl="lol")
		# self.deleteRowsByValue(dlState="lol")

		self.getRowsByValue(dbId=5)
		self.getRowsByValue(sourceUrl="5")
		self.getRowsByValue(sourceUrl="5", limitByKey=False)


	def getRowsByValue(self, limitByKey=True, **kwargs):

		cur = kwargs.pop("cur", None)

		if limitByKey and self.tableKey:
			kwargs["sourceSite"] = self.tableKey


		where = self.sqlBuildConditional(**kwargs)

		wantCols = (
				self.table.dbid,
				self.table.dlstate,
				self.table.sourceurl,
				self.table.retreivaltime,
				self.table.lastupdate,
				self.table.sourceid,
				self.table.seriesname,
				self.table.filename,
				self.table.originname,
				self.table.downloadpath,
				self.table.flags,
				self.table.tags,
				self.table.note
				)

		query = self.table.select(*wantCols, order_by=sql.Desc(self.table.retreivaltime), where=where)

		query, quargs = tuple(query)

		if self.QUERY_DEBUG:
			print("Query = ", query)
			print("args = ", quargs)

		if cur is not None:
			cur.execute(query, quargs)
			rets = cur.fetchall()
		else:
			with self.transaction(commit=False) as cur:
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
		# print("Getting row", kwargs)
		row = self.getRowByValue(**kwargs)
		if not row:
			raise ValueError("Row specified does not exist!")

		if row["tags"]:
			existingTags = set(row["tags"].split(" "))
		else:
			existingTags = set()

		newTags = set()
		for tagTemp in set(tags.split(" ")):

			# colon literals (":") break the `tsvector` index. Remove them (they're kinda pointless anyways)
			tagTemp = tagTemp.replace("&", "_")   \
							.replace(":", "_")    \
							.strip(".")           \
							.lower()
			newTags.add(tagTemp)


		tags = existingTags | newTags

		# make the tag ordering determistic by converting to a list, and sorting.
		tags = list(tags)
		tags.sort()

		tagStr = " ".join(tags)
		while "  " in tagStr:
			tagStr = tagStr.replace("  ", " ")
		tagStr = tagStr.lower()
		self.updateDbEntry(row["sourceUrl"], tags=tagStr)




	# Insert new tags specified as a string kwarg (tags="tag Str") into the tags listing for the specified item
	def removeTags(self, **kwargs):
		validCols = ["dbId", "sourceUrl", "dlState"]
		if not any([name in kwargs for name in validCols]):
			raise ValueError("addTags requires at least one fully-qualified argument (%s). Passed args = '%s'" % (validCols, kwargs))

		if not "tags" in kwargs:
			raise ValueError("You have to specify tags you want to add as a kwarg! '%s'" % (kwargs))

		tags = kwargs.pop("tags")
		row = self.getRowByValue(**kwargs)
		if not row:
			raise ValueError("Row specified does not exist!")

		if not row["tags"]:
			existingTags = set(row["tags"].split(" "))
		else:
			existingTags = set()

		newTags = set(tags.split(" "))

		tags = existingTags - newTags

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



	# ---------------------------------------------------------------------------------------------------------------------------------------------------------
	# DB Management
	# ---------------------------------------------------------------------------------------------------------------------------------------------------------

	def checkInitPrimaryDb(self):
		with self.transaction() as cur:

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
				("%s_source_index"           % self.tableName, self.tableName, '''CREATE INDEX %s ON %s (sourceSite                                            );'''  ),
				("%s_time_index"             % self.tableName, self.tableName, '''CREATE INDEX %s ON %s (retreivalTime                                         );'''  ),
				("%s_lastUpdate_index"       % self.tableName, self.tableName, '''CREATE INDEX %s ON %s (lastUpdate                                            );'''  ),
				("%s_url_index"              % self.tableName, self.tableName, '''CREATE INDEX %s ON %s (sourceUrl                                             );'''  ),
				("%s_seriesName_index"       % self.tableName, self.tableName, '''CREATE INDEX %s ON %s (seriesName                                            );'''  ),
				("%s_tags_index"             % self.tableName, self.tableName, '''CREATE INDEX %s ON %s (tags                                                  );'''  ),
				("%s_flags_index"            % self.tableName, self.tableName, '''CREATE INDEX %s ON %s (flags                                                 );'''  ),
				("%s_dlState_index"          % self.tableName, self.tableName, '''CREATE INDEX %s ON %s (dlState                                               );'''  ),
				("%s_originName_index"       % self.tableName, self.tableName, '''CREATE INDEX %s ON %s (originName                                            );'''  ),
				("%s_aggregate_index"        % self.tableName, self.tableName, '''CREATE INDEX %s ON %s (seriesName, retreivalTime, dbId                       );'''  ),
				('%s_special_full_idx'       % self.tableName, self.tableName, '''CREATE INDEX %s ON %s (retreivaltime DESC, seriesName DESC, dbid             );'''  ),
				('%s_special_granulated_idx' % self.tableName, self.tableName, '''CREATE INDEX %s ON %s (sourceSite, retreivaltime DESC, seriesName DESC, dbid );'''  ),

				# Create a ::tsvector GiN index on the tags column, so we can search by tags quickly.
				("%s_tags_gin_index"         % self.tableName, self.tableName, '''CREATE INDEX %s ON %s USING gin((lower(tags)::tsvector)                      );'''  ),
				# "%s_tags_gin_index"         % self.tableName, self.tableName, '''CREATE INDEX mangaitems_tags_gin_index ON mangaitems gin((lower(tags)::tsvector));'''
			]

			# CREATE INDEX hentaiitems_tags_gin_index ON hentaiitems USING gin((lower(tags)::tsvector));
			# CREATE INDEX mangaitems_tags_gin_index ON mangaitems USING gin((lower(tags)::tsvector));
			# CREATE INDEX hentaiitems_oname_trigram ON hentaiitems USING gin (originname gin_trgm_ops);
			# CREATE INDEX mangaitems_oname_trigram ON mangaitems USING gin (originname gin_trgm_ops);
			# UPDATE hentaiitems SET tags = replace(tags, ':', '_')
			# UPDATE hentaiitems SET tags = lower(tags)

			for name, table, nameFormat in indexes:
				if not name.lower() in haveIndexes:
					cur.execute(nameFormat % (name, table))



		self.log.info("Retreived page database created")


if __name__ == "__main__":
	import settings
	class TestClass(ScraperDbBase):



		pluginName = "Wat?"
		loggerPath = "Wat?"
		dbName = settings.DATABASE_DB_NAME
		tableKey = "test"
		tableName = "MangaItems"

		def go(self):
			print("Go?")



	import utilities.testBase as tb

	with tb.testSetup():
		obj = TestClass()
		obj.QUERY_DEBUG = True
		print(obj)
		obj.test()


