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

import urllib.parse
%>




<%def name="renderRow(rowData)">
	<%
	dbid, itemname, itemtable, readingprogress, availprogress, ratingVal, sourceSite = rowData


	rating = ''
	if ratingVal >= 0:
		rating = '%s' % ratingVal

	reading = ''
	if readingprogress >= 0:
		reading = '%s' % readingprogress

	available = ''
	if availprogress >= 0:
		available = '%s' % availprogress

	mapper = {
		'books_lndb': 'LNDB',
		'MangaSeries': 'MangaUpdates',
	}

	if sourceSite in mapper:
		sourceSite = mapper[sourceSite]

	%>
	<tr>
		<td>${sourceSite}</td>
		<td>${ut.makeBookItemLink(itemname, itemname)}</td>
		<td>${rating}</td>
		<td>${reading}</td>
		<td>${available}</td>
	</tr>
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

	query = '''SELECT
			book_series.dbid,
			book_series.itemname,
			book_series.itemtable,
			book_series.readingprogress,
			book_series.availprogress,
			book_series.rating,
			book_series_table_links.tablename
		FROM book_series
		INNER JOIN book_series_table_links
		ON book_series.itemtable = book_series_table_links.dbid
		{srcFilter}
		ORDER BY book_series.itemname;'''.format(srcFilter=srcFilter)

	print(query, args)
	cursor.execute(query, args)

	seriesList = cursor.fetchall()

	%>

	TODO: Add filtering stuff!

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



