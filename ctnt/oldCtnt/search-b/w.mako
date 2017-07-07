## -*- coding: utf-8 -*-
<!DOCTYPE html>

<%
startTime = time.time()
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


<%namespace name="tableGenerators" file="/gentable.mako"/>
<%namespace name="sideBar"         file="/gensidebar.mako"/>
<%namespace name="ut"              file="/utilities.mako"/>
<%namespace name="ap"              file="/activePlugins.mako"/>
<%namespace name="searchFuncs"     file="/search-h/searchFuncs.mako"/>

<html>
<head>
	<title>WAT WAT IN THE BATT</title>

	${ut.headerBase()}

</head>
<body>



<%

if 'q' in request.params:
	searchterm = request.params['q']

	# MangaUpdates denotes novels by inserting "(Novel)" in the title. That makes the search results
	# kind of cranky, so strip that out.
	searchterm = searchterm.replace("(Novel)", "")
	searchterm = searchterm.strip()

	searchFuncs.genSearchBody(searchterm, 'book_western_items')
else:
	searchFuncs.genSearchError("No search query specified!")

%>


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