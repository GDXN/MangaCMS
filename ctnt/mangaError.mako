## -*- coding: utf-8 -*-
<!DOCTYPE html>

<%!
import time
import urllib.parse

import sql
import sql.aggregate
import sql.conditionals

%>

<%startTime = time.time()%>

<%namespace name="tableGenerators" file="gentable.mako"/>
<%namespace name="sideBar"         file="gensidebar.mako"/>
<%namespace name="ap"              file="activePlugins.mako"/>

<%namespace name="ut"              file="utilities.mako"/>



<%



limit = 200
pageNo = 0


if "page" in request.params:
	try:
		pageNo = int(request.params["page"])-1
	except ValueError:
		pass

if pageNo < 0:
	pageNo = 0


offset = limit * pageNo


prevPage = request.params.copy();
prevPage["page"] = pageNo
nextPage = request.params.copy();
nextPage["page"] = pageNo+2



if "sourceSite" in request.params:
	tmpSource = request.params.getall("sourceSite")
	sourceFilter = [item for item in tmpSource if item in ap.attr.active]
else:
	sourceFilter = []



sourceName = 'Manga Items'

sourceFilter = None
divId      = ""

print("sourceFilter", sourceFilter)

%>


<html>
	<head>
		<title>WAT WAT IN THE BATT</title>
		${ut.headerBase()}


	</head>
	<body>

		<div>

			${sideBar.getSideBar(sqlCon)}
			<div class="maindiv">
				<div class="subdiv ${divId}">

						<div class="contentdiv">
							<h3>${sourceName}</h3>
							${tableGenerators.genLegendTable()}
							${tableGenerators.genMangaTable(tableKey=sourceFilter, limit=limit, offset=offset, getErrored=True)}
						</div>

						% if pageNo > 0:
							<span class="pageChangeButton" style='float:left;'>
								<a href="mangaError?${urllib.parse.urlencode(prevPage)}">prev</a>
							</span>
						% endif
						<span class="pageChangeButton" style='float:right;'>
							<a href="mangaError?${urllib.parse.urlencode(nextPage)}">next</a>
						</span>

						</div>
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


