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

import urllib.parse
%>


<body>

<%

cur = sqlCon.cursor()
cur.execute("""SELECT DISTINCT(netloc) FROM book_western_items WHERE istext=TRUE ORDER BY netloc;""")
ret = cur.fetchall()
print("Dictinct = ", ret)



%>

<div>
	${sideBar.getSideBar(sqlCon)}
	<div class="maindiv">

		<div class="subdiv">
			<div class="contentdiv">
				<h2>BookTrie!</h2>
				<%
				cursor = sqlCon.cursor()
				%>

				% for srcDomain, in ret:
					<%
					if not srcDomain:
						srcDomain = ''
					treeRender.renderTree(srcDomain)
					%>
				% endfor

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