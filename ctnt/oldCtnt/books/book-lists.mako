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


<%def name="renderList(listName)">
	<%


	%>
	List: ${listName}
</%def>


<%def name="renderListTable()">
	<%

	cursor = sqlCon.cursor()

	cursor.execute("""SELECT listname FROM books_lndb_series_list;""")
	lists = cursor.fetchall()

	%>




	<div>

		% if not lists:
			<tr>
				<td>
					No Lists!
				</td>
			</tr>
		% else:
			<table border="1px">
				<col width="400">
				<tr>
					<th>
						All Lists:
					</th>
				</tr>
				% for list in lists:
					<tr>
						<td>
							${list}
						</td>
					</tr>
				% endfor
			</table>
		% endif
	</div>

</%def>

<%def name="renderListControls()">
wat
</%def>

<%def name="renderAllLists()">
	<h2>Book Lists</h2>
	<%
	renderListTable()
	renderListControls()
	%>
</%def>




<%
listName = ut.getUrlParam('list')
%>

<body>


	<div>
		${sideBar.getSideBar(sqlCon)}
		<div class="maindiv">

			<div class="subdiv">
				<div class="contentdiv">
					<%
					if listName:
						renderList(listName)
					else:
						renderAllLists()
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