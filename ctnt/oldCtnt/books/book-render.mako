## -*- coding: utf-8 -*-

<%namespace name="tableGenerators" file="/gentable.mako"/>
<%namespace name="sideBar"         file="/gensidebar.mako"/>
<%namespace name="ut"              file="/utilities.mako"/>
<%namespace name="ap"              file="/activePlugins.mako"/>


<%!
import time
import datetime
from babel.dates import format_timedelta
import os.path
import settings
import string
import nameTools as nt

import urllib.parse
%>



<%def name="stripNovel(inStr)">
	<%
	if inStr.endswith("(Novel)"):
		inStr = inStr[:-len("(Novel)")]
	return inStr
	%>
</%def>

<%def name="renderRow(rowDict)">
	<%
	## dbid, itemname, itemtable, readingprogress, availprogress, ratingVal, sourceSite = rowDict

	itemname = stripNovel(rowDict['itemname'])


	rating = ''
	if rowDict['ratingVal'] >= 0:
		rating = '%s' % rowDict['ratingVal']

	reading = ''
	if rowDict['readingprogress'] >= 0:
		reading = '%s' % rowDict['readingprogress']

	available = ''
	if rowDict['availprogress'] >= 0:
		available = '%s' % rowDict['availprogress']




	mapper = {
		'books_lndb': 'LNDB',
		'MangaSeries': 'MU',
	}

	sources = []
	for source in rowDict['sourceSite']:
		if source in mapper:
			sources.append(mapper[source])
		else:
			sources.append(source)
	sources = ", ".join(sources)


	%>
	<tr>
		<td>${sources}</td>
		<td>${ut.makeBookIdLink(rowDict['dbid'], itemname)}</td>

		% if 'listName' in rowDict:
			<%
			list = ''
			if rowDict['listName']:
				list = rowDict['listName']
			%>
			<td>${ut.makeBookListLink(list, list)}</td>
		% endif

		<td>${rating}</td>
		<td>${reading}</td>
		<td>${available}</td>
	</tr>
</%def>


<%def name="aggregateSourceList(sourceItems, noList=False)">
	<%

	itemNames = ['dbid', 'itemname', 'itemtable', 'readingprogress', 'availprogress', 'ratingVal', 'sourceSite', 'listName']

	## If we don't want the listName entry, pop it away
	if noList:
		itemNames.pop()

	maxItems = ['readingprogress', 'availprogress', 'ratingVal']

	ret = {}

	for data in sourceItems:
		row = dict(zip(itemNames, data))
		cleanName = stripNovel(row['itemname'])
		cleanName = nt.prepFilenameForMatching(cleanName)
		if cleanName in ret:
			ret[cleanName]['sourceSite'].add(row['sourceSite'])

			## Take the maximum value version of the reading/available/rating keys
			for key in maxItems:
				if row[key] > ret[cleanName][key]:
					ret[cleanName][key] = row[key]

			## And always use the /smaller/ dbid key.
			ret[cleanName]['dbid'] = min((row['dbid'], ret[cleanName]['dbid']))

		else:
			row['sourceSite'] = set([row['sourceSite']])

			ret[cleanName] = row

	sortRet = list(ret.values())
	sortRet.sort(key= lambda k: k['itemname'])
	return sortRet
	%>
</%def>


<%def name="renderBookList(listFilter=None)">
	<%


	if listFilter:
		srcFilter = '''WHERE book_series_list_entries.listname = %s'''
		args = (listFilter, )
	else:
		srcFilter = ''
		args = ()

	cursor = sqlCon.cursor()

	query = '''SELECT
			book_series.dbid,
			book_series.itemname,
			book_series.itemtable,
			book_series.readingprogress,
			book_series.availprogress,
			book_series.rating,
			book_series_list_entries.listname
		FROM book_series_list_entries
		INNER JOIN book_series
		ON book_series.dbid = book_series_list_entries.seriesid
		{srcFilter};'''.format(srcFilter=srcFilter)

	print(query)
	print(args	)
	cursor.execute(query, args)

	seriesList = cursor.fetchall()
	seriesList = aggregateSourceList(seriesList, noList=bool(listFilter))

	%>


	<div>

		<table border="1px">
			<tr>
					<th class="padded" width="90">Source</th>
					<th class="padded" width="400">Full Name</th>
					<th class="padded" width="30">Rating</th>
					<th class="padded" width="30">Read-To Chapter</th>
					<th class="padded" width="30">Latest Chapter</th>
			</tr>

			<%
			for series in seriesList:
				renderRow(series)
			%>

		</table>

	</div>
</%def>



<%def name="renderBookSeries(tableFilter=None)">
	<%


	if tableFilter:
		srcFilter = '''AND book_series_table_links.tablename = %s'''
		args = (tableFilter, )
	else:
		srcFilter = ''
		args = ()
	cursor = sqlCon.cursor()

	# Fetch all the book items.
	# Join in the source table name, and also the list (if any)
	# EXPLAIN ANALYZE says ~4.3 ms.
	# The INNER portion of the INNER JOIN is probably unnecessary, as
	# that row has a foreign key constraint into the table it's being
	# joined with, but whatever.
	query = '''SELECT
			book_series.dbid,
			book_series.itemname,
			book_series.itemtable,
			book_series.readingprogress,
			book_series.availprogress,
			book_series.rating,
			book_series_table_links.tablename,
			book_series_list_entries.listname
		FROM book_series
		INNER JOIN book_series_table_links
			ON book_series.itemtable = book_series_table_links.dbid
		LEFT OUTER JOIN book_series_list_entries
			ON book_series.dbid = book_series_list_entries.seriesid
		{srcFilter};'''.format(srcFilter=srcFilter)

	cursor.execute(query, args)

	seriesList = cursor.fetchall()
	seriesList = aggregateSourceList(seriesList)

	%>

	TODO: Add filtering stuff!

	<div>

		<table border="1px">
			<tr>
					<th class="padded" width="90">Source</th>
					<th class="padded" width="400">Full Name</th>
					<th class="padded" width="30">List</th>
					<th class="padded" width="30">Rating</th>
					<th class="padded" width="30">Read-To Chapter</th>
					<th class="padded" width="30">Latest Chapter</th>
			</tr>

			<%
			for series in seriesList:
				renderRow(series)
			%>

		</table>

	</div>
</%def>



