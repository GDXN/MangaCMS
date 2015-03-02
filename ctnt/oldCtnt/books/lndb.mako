## -*- coding: utf-8 -*-
<!DOCTYPE html>


<%namespace name="tableGenerators" file="/gentable.mako"/>
<%namespace name="sideBar"         file="/gensidebar.mako"/>
<%namespace name="ut"              file="/utilities.mako"/>
<%namespace name="ap"              file="/activePlugins.mako"/>
<%namespace name="treeRender"      file="/books/render.mako"/>

<html>
<head>
	<title>WAT WAT IN THE BATT</title>

	${ut.headerBase()}

	<script type="text/javascript">
		$(document).ready(function() {
		// Tooltip only Text

	</script>

	<link rel="stylesheet" href="/books/treeview.css">

</head>


<%
startTime = time.time()
# print("Rendering begun")
%>


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


<%def name="renderBookSeries()">
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

	cursor.execute("SELECT dbid, ctitle, readingprogress, availprogress, rating FROM books_lndb WHERE seriesentry=TRUE ORDER BY ctitle;")
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



<body>


<div>
	${sideBar.getSideBar(sqlCon)}
	<div class="maindiv">

		<div class="subdiv">
			<div class="contentdiv">
				<h2>LNDB Content!</h2>

				<%
				renderBookSeries()
				%>
				## % for srcKey, srcName in settings.bookSources:
				## 	<div class="css-treeview">
				## 		${renderTreeRoot(srcKey, srcName)}
				## 	</div>
				## 	<hr>
				## % endfor

			</div>

		</div>
	</div>
</div>


<%
fsInfo = os.statvfs(settings.mangaFolders[1]["dir"])
stopTime = time.time()
timeDelta = stopTime - startTime
%>

<p>
	This page rendered in ${timeDelta} seconds.<br>
	Disk = ${int((fsInfo.f_bsize*fsInfo.f_bavail) / (1024*1024))/1000.0} GB of  ${int((fsInfo.f_bsize*fsInfo.f_blocks) / (1024*1024))/1000.0} GB Free.
</p>

</body>
</html>