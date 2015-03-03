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
import traceback
import string

import urllib.parse
%>

<%
startTime = time.time()
# print("Rendering begun")
%>

<%def name="renderRow(rowData)">
	<h2>LNDB Book Series: </h2>
</%def>

<%def name="renderError(rowData)">
	<h2>LNDB Book Series: </h2>
</%def>



<%def name="queryError(errStr=None)">
	<br>

	<div class="errorPattern">
		<h2>Content Error!</h2>
		<p>${errStr}</p>

	</div>




</%def>


<%def name="renderId(itemId)">
	<%
	print("LNDB Item: ------------------------", itemId)

	cursor = sqlCon.cursor()

	cursor.execute("""SELECT books_lndb.dbid,
							books_lndb.changestate,
							books_lndb.ctitle,
							books_lndb.otitle,
							books_lndb.vtitle,
							books_lndb.jtitle,
							books_lndb.jvtitle,
							books_lndb.series,
							books_lndb.pub,
							books_lndb.label,
							books_lndb.volno,
							books_lndb.author,
							books_lndb.illust,
							books_lndb.target,
							books_lndb.description,
							books_lndb.seriesentry,
							books_lndb.covers,
							books_lndb.readingprogress,
							books_lndb.availprogress,
							books_lndb.rating,
							books_lndb.reldate,
							books_lndb.lastchanged,
							books_lndb.lastchecked,
							books_lndb.firstseen,
							listname
						FROM books_lndb
						LEFT JOIN books_lndb_series_list ON books_lndb_series_list.seriesId = books_lndb.dbid
						WHERE books_lndb.dbid=%s;""", (itemId, ))
	item = cursor.fetchone()

	print("Return:", item)

	dbid,                    \
			changestate,     \
			ctitle,          \
			otitle,          \
			vtitle,          \
			jtitle,          \
			jvtitle,         \
			series,          \
			pub,             \
			label,           \
			volno,           \
			author,          \
			illust,          \
			target,          \
			description,     \
			seriesentry,     \
			covers,          \
			readingprogress, \
			availprogress,   \
			rating,          \
			reldate,         \
			lastchanged,     \
			lastchecked,     \
			firstseen,       \
			listname = item


	%>


	<h2>Series: ${ctitle}</h2>
	<div style="float:right">
		<div class="lightRect itemInfoBox">
			List: ${listname}
		</div>
	</div>
	<div>
		<table>

			<col width="200">
			<col width="200">
			<tr>
				<td>Series Name:</td>
				<td>${ctitle}</td>
			</tr>

			<tr>
				<td>Japanese Name:</td>
				<td>${jtitle}</td>
			</tr>

			<tr>
				<td>Author:</td>
				<td>${author}</td>
			</tr>

			<tr>
				<td>Illustrator:</td>
				<td>${illust}</td>
			</tr>
			<tr>
				<td>Target Demographic:</td>
				<td>${target}</td>
			</tr>

			<tr>
				<td>Published Volumes:</td>
				<td>${volno}</td>
			</tr>
		</table>
		${item}
	</div>
</%def>


<%def name="render()">
	<%


	if "dbid" in request.params:
		try:
			seriesId = int(request.params["dbid"])
			renderId(seriesId)
			return
		except:
			traceback.print_exc()
			pass

	queryError("No item ID in URL!")

	%>

</%def>


<body>


	<div>
		${sideBar.getSideBar(sqlCon)}
		<div class="maindiv">

			<div class="subdiv">
				<div class="contentdiv">
					<%
					render()

					%>


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