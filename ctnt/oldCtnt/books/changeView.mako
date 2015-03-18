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
<%def name="renderRow(row)">
	<%
		src, url, change, title, changeDate = row

		changeDate = time.strftime('%y-%m-%d %H:%M', time.localtime(changeDate))
	%>
	<tr>
		<td>
			${changeDate}
		</td>
		<td>
			${src.title()}
		</td>
		<td>
			${'%0.2f' % change}%
		</td>
		<td>
			<div id='rowLink'><a href='/books/render?url=${urllib.parse.quote(url)}'>${title}</a></div>
		</td>
	</tr>
</%def>


<%def name="renderChangeTable(all=False)">
	<%
	cur = sqlCon.cursor()
	cur.execute("BEGIN")
	if all:
		cur.execute("SELECT src, url, change, title, changeDate FROM book_changes ORDER BY changeDate DESC limit 200;")
	else:
		cur.execute("SELECT src, url, change, title, changeDate FROM book_changes WHERE change > %s ORDER BY changeDate DESC limit 200;", (2, ))
	ret = cur.fetchall()
	cur.execute("COMMIT")
	%>
	<div>
		<table border="1px" style="width: 100%;">
			<tr>
					<th class="uncoloured" style="width: 102px; min-width: 102px;">Date</th>
					<th class="uncoloured" style="width: 60px; min-width: 60px;">Src</th>
					<th class="uncoloured" style="width: 60px; min-width: 60px;">Change</th>
					<th class="uncoloured">BaseName</th>
			</tr>
			% for row in ret:
				${renderRow(row)}
			% endfor
		</table>
	</div>

</%def>


<body>
<div>
	${sideBar.getSideBar(sqlCon)}
	<div class="maindiv">

		<div class="subdiv">
			<div class="contentdiv">
				<h2>Book Updates!</h2>
				${renderChangeTable()}

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