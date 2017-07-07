## -*- coding: utf-8 -*-
<!DOCTYPE html>

<%namespace name="sideBar"         file="/gensidebar.mako"/>
<%namespace name="ut"              file="/utilities.mako"/>
<%namespace name="render"          file="/feeds/render.mako"/>


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

<%

rssItemId = ut.getUrlParam('entry')


%>
<body>
<div>
	${sideBar.getSideBar(sqlCon)}
	<div class="maindiv">

		<div class="subdiv">
			<div class="contentdiv">
				<h2>Rss Item</h2>

				<%
				if rssItemId:
					render.itemId(rssItemId)
				else:
					ut.errorDiv("No item ID specified!")

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