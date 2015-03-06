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
	dbid, ctitle, readingprogress, availprogress, ratingVal = rowData


	rating = ''
	if ratingVal >= 0:
		rating = '%s' % ratingVal

	reading = ''
	if readingprogress >= 0:
		reading = '%s' % readingprogress

	available = ''
	if availprogress >= 0:
		available = '%s' % availprogress

	%>
	<tr>
		<td>${ut.makeLndbItemLink(dbid, ctitle)}</td>
		<td>${rating}</td>
		<td>${reading}</td>
		<td>${available}</td>
	</tr>
</%def>


<%def name="renderBookSeries(tableName)">
	<%


	## dbid            | integer          | not null default nextval('books_lndb_dbid_seq'::regclass)
	## changestate     | integer          | default 0
	## ctitle          | citext           |
	## otitle          | text             |
	## vtitle          | text             |
	## jtitle          | text             |
	## jvtitle         | text             |
	## series          | text             |
	## pub             | text             |
	## label           | text             |
	## volno           | citext           |
	## author          | text             |
	## illust          | text             |
	## target          | citext           |
	## description     | text             |
	## seriesentry     | boolean          |
	## covers          | text[]           |
	## readingprogress | integer          |
	## availprogress   | integer          |
	## rating          | integer          |
	## reldate         | double precision |
	## lastchanged     | double precision |
	## lastchecked     | double precision |
	## firstseen       | double precision | not null


	## rootKey, rootTitle

	cursor = sqlCon.cursor()

	cursor.execute("SELECT dbid, ctitle, readingprogress, availprogress, rating FROM {table} WHERE seriesentry=TRUE ORDER BY ctitle;".format(table=tableName))
	seriesList = cursor.fetchall()

	%>

	TODO: Add filtering stuff!

	<div>

		<table border="1px">
			<tr>
					<th class="padded" width="600">Full Name</th>
					<th class="padded" width="30">Rating</th>
					<th class="padded" width="30">Latest Chapter</th>
					<th class="padded" width="30">Read-To Chapter</th>
			</tr>

			<%
			for series in seriesList:
				renderRow(series)
			%>

		</table>

	</div>
</%def>


