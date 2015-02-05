## -*- coding: utf-8 -*-
<!DOCTYPE html>

<%startTime = time.time()%>

<%namespace name="tableGenerators" file="gentable.mako"/>
<%namespace name="sideBar"         file="gensidebar.mako"/>
<%namespace name="ap"              file="activePlugins.mako"/>

<%namespace name="ut"              file="utilities.mako"/>



<%!
import time
import urllib.parse
import settings

import sql
import sql.operators as sqlo

table = sql.Table("mangaitems")

cols = (
		table.dbId,
		table.dlState,
		table.sourceSite,
		table.sourceUrl,
		table.retreivalTime,
		table.sourceId,
		table.seriesName,
		table.fileName,
		table.originName,
		table.downloadPath,
		table.flags,
		table.tags,
		table.note
	)

%>


<%

def sqlalchemy_test():

	import sqlalchemy as sa
	import sqlalchemy.ext.declarative as dec
	import sqlalchemy.engine.url as saurl
	import sqlalchemy.orm as saorm
	import sqlalchemy.schema as sch
	import sqlalchemy.ext.automap as amap

	import inspect
	engine_conf = saurl.URL(drivername='postgresql',
							username = settings.DATABASE_USER,
							password = settings.DATABASE_PASS,
							database = settings.DATABASE_DB_NAME
							# host = settings.DATABASE_IP,
							)


	engine = sa.create_engine(engine_conf)
	session = saorm.Session(engine)


	# reflect the tables
	Base = amap.automap_base()
	Base.prepare(engine, reflect=True)

	# mapped classes are now created with names by default
	# matching that of the table name.

	print(Base)
	print(Base.classes)
	print(Base.classes.mangaitems)
	print(inspect.getmro(Base.classes.mangaitems))

	mangaTable = Base.classes.mangaitems
	print("Querying")
	first = session.query(mangaTable).first()
	print(first)
	print(dir(first))
	print(first.dbid)



	# User = Base.classes.user
	# Address = Base.classes.address

	# session = Session(engine)

	# # rudimentary relationships are produced
	# # session.add(Address(email_address="foo@bar.com", user=User(name="foo")))
	# # session.commit()

	# # collection-based relationships are by default named
	# # "<classname>_collection"
	# print (u1.address_collection)




# sqlalchemy_test()


def buildMangaQuery(cols, tableKey=None, tagsFilter=None, seriesFilter=None, seriesName=None):

	query = table.select(*cols, order_by = sql.Desc(table.retreivalTime))


	if tableKey == None:
		pass

	elif type(tableKey) is str:
		query.where = (table.sourceSite == tableKey)

	elif type(tableKey) is list or type(tableKey) is tuple:
		for key in tableKey:
			if not query.where:
				query.where = (table.sourceSite == key)
			else:
				query.where |= (table.sourceSite == key)

	else:
		raise ValueError("Invalid table-key type")

	tagsFilterArr = []
	if tagsFilter != None:
		for tag in tagsFilter:

			if not query.where:
				query.where = sqlo.Like(table.tags, key)
			else:
				query.where |= sqlo.Like(table.tags, key)


	seriesFilterArr = []
	if seriesFilter != None:
		for key in seriesFilter:

			if not query.where:
				query.where = sqlo.Like(table.seriesName, key)
			else:
				query.where &= sqlo.Like(table.seriesName, key)


	seriesNameArr = []
	if seriesName != None:
			if not query.where:
				query.where = (table.seriesName == seriesName)
			else:
				query.where &= (table.seriesName == seriesName)


	return query

def sql_test():

	table = sql.Table("mangaitems")
	x = "wat"

	cols = (
			table.dbId,
			table.dlState,
			table.sourceSite,
			table.sourceUrl,
			table.retreivalTime,
			table.sourceId,
			table.seriesName,
			table.fileName,
			table.originName,
			table.downloadPath,
			table.flags,
			table.tags,
			table.note
		)
	select = table.select(*cols,
		order_by=sql.Desc(table.retreivalTime))

	print("WHERE", select.where)
	select.where = (table.sourceSite == "lol") | (table.sourceSite == 'wat')
	print("WHERE", select.where)
	select.where &= (table.sourceSite == 'herp') & (table.sourceSite == 'derp')
	print("WHERE", select.where)



	print("Tablezzzzz", table)
	print("select", tuple(select))

	buildMangaQuery(cols, tableKey=["bt", "wat"], tagsFilter=['wat'], seriesName="lolercopter")

sql_test()


%>
WAT?
