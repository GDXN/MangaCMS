## -*- coding: utf-8 -*-
<!DOCTYPE html>
<html>
<head>
	<title>WAT WAT IN THE BATT</title>
	<link rel="stylesheet" href="style.css">
</head>

<%startTime = time.time()%>

<%namespace name="tableGenerators" file="gentable.mako"/>
<%namespace name="sideBar" file="gensidebar.mako"/>

<%!
# Module level!
import time
import datetime
from babel.dates import format_timedelta
import os.path

import urllib.parse
%>

<%
cur = sqlCon.cursor()

show = "all"
if "valid" in request.params:
	if request.params["valid"] == ["false"]:
		show = "invalid"

	elif request.params["valid"] == ["true"]:
		show = "valid"

limit = 500

pageNo = 0

try:
	pageNo = int(request.params["page"])-1
except ValueError:
	pass
except KeyError:
	pass

if pageNo < 0:
	pageNo = 0

tagsFilter = None
seriesFilter = None

if "byTag" in request.params:
	tagsFilter = request.params.getall("byTag")
if "bySeries" in request.params:
	seriesFilter = request.params.getall("bySeries")


offset = limit * pageNo


prevPage = request.params.copy();
prevPage["page"] = pageNo
nextPage = request.params.copy();
nextPage["page"] = pageNo+2


%>

<body>

<div>

	${sideBar.getSideBar(sqlCon)}
	<div class="maindiv">
		<div class="subdiv fuFuId">
			<div class="contentdiv">
				<h3>Fufufuu</h3>
				<!-- <div class="" style="white-space:nowrap; display: inline-block; margin-left: 80px;">
					Filter download Status:
					<ul style="width: 100px;">

						<li> <a href="itemsFufufuu?valid=true">Successful</a></li>
						<li> <a href="itemsFufufuu?valid=false">Failed</a></li>
						<li> <a href="itemsFufufuu">All</a></li>
					</ul>
				</div>
				<div class="" style="white-space:nowrap; display: inline-block;">
					Retry broken links:<br>
					<a href="itemsFufufuu?reset-links=all-links">Reset all</a>
				</div> -->
				${tableGenerators.genLegendTable()}
				${tableGenerators.genFuuTable(offset=pageNo, tagsFilter=tagsFilter, seriesFilter=seriesFilter)}
			</div>
			% if pageNo > 0:
				<span class="pageChangeButton" style='float:left;'>
					<a href="itemsFufufuu?${urllib.parse.urlencode(prevPage)}">prev</a>
				</span>
			% endif
			<span class="pageChangeButton" style='float:right;'>
				<a href="itemsFufufuu?${urllib.parse.urlencode(nextPage)}">next</a>
			</span>



		</div>

	</div>
<div>

<%
stopTime = time.time()
timeDelta = stopTime - startTime
%>

<p>This page rendered in ${timeDelta} seconds.</p>

</body>
</html>