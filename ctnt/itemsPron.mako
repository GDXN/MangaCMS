## -*- coding: utf-8 -*-
<!DOCTYPE html>

<%namespace name="tableGenerators" file="gentable.mako"/>
<%namespace name="sideBar"         file="gensidebar.mako"/>
<%namespace name="ap"              file="activePlugins.mako"/>
<%namespace name="ut"              file="utilities.mako"/>

<html>
<head>
	<title>WAT WAT IN THE BATT</title>
	${ut.headerBase()}
</head>

<%startTime = time.time()%>


<%!
# Module level!
import time
import datetime
from babel.dates import format_timedelta
import os.path




import re

import urllib.parse

import nameTools as nt

def compactDateStr(dateStr):
	dateStr = dateStr.replace("months", "mo")
	dateStr = dateStr.replace("month", "mo")
	dateStr = dateStr.replace("weeks", "w")
	dateStr = dateStr.replace("week", "w")
	dateStr = dateStr.replace("days", "d")
	dateStr = dateStr.replace("day", "d")
	dateStr = dateStr.replace("hours", "hr")
	dateStr = dateStr.replace("hour", "hr")
	dateStr = dateStr.replace("minutes", "m")
	dateStr = dateStr.replace("seconds", "s")
	return dateStr

def fSizeToStr(fSize):
	if fSize < 1.0e7:
		fStr = fSize/1.0e3
		fStr = "%d K" % int(fStr)
	else:
		fStr = fSize/1.0e6
		fStr = "%0.2f M" % fStr
	return fStr


colours = {
	# Download Status
	"failed"          : "000000",
	"no matching dir" : "FF9999",
	"moved"           : "FFFF99",
	"downloaded"      : "99FF99",
	"processing"      : "9999FF",
	"queued"          : "FF77FF",
	"created-dir"     : "FFE4B2",
	"not checked"     : "FFFFFF",

	# Categories

	"valid category"  : "FFFFFF",
	"bad category"    : "999999"
	}

def mergeDict(dict1,*dicts):
	for dict2 in dicts:
		dict1.update(dict2)
	return dict1

%>

<%

limit = 200

pageNo = 0



try:
	pageNo = int(request.params["page"])-1
except ValueError:
	pass
except KeyError:
	pass
except NameError:
	pass

if pageNo < 0:
	pageNo = 0


offset = limit * pageNo



tagsFilter = None
seriesFilter = None

if "byTag" in request.params:
	tagsFilter = request.params.getall("byTag")
if "bySeries" in request.params:
	seriesFilter = request.params.getall("bySeries")

if "sourceSite" in request.params:
	tmpSource = request.params.getall("sourceSite")
	sourceFilter = [item for item in tmpSource if item in ap.attr.activePorn]
else:
	sourceFilter = []



prevPage = request.params.copy()
prevPage["page"] = pageNo
nextPage = request.params.copy()
nextPage["page"] = pageNo+2


sourceItems = {}
for item in ap.attr.sidebarItemList:
	if item["dictKey"] in sourceFilter:
		sourceItems[item["dictKey"]] = item


if len(sourceFilter) > 1 or len(sourceFilter) == 0:
	divId = "djMoeId"
	sourceName = "Aggregate Pron Items"
	sourceFilter = None
else:
	lut = sourceItems[sourceFilter[0]]

	divId      = lut["cssClass"]
	sourceName = lut["name"] + " Items"

%>

<body>

<div>

	${sideBar.getSideBar(sqlCon)}
	<div class="maindiv">
		<div class="subdiv ${divId}">
			<div class="contentdiv">
				<h3>${sourceName}</h3>

				Query =<br>
				% for key in request.params.keys():
					% if key != "page":
						${key} ${request.params.getall(key)}<br>
					% endif
				% endfor
				${tableGenerators.genPronTable(siteSource=sourceFilter, offset=pageNo, tagsFilter=tagsFilter, seriesFilter=seriesFilter)}
			</div>

			% if pageNo > 0:
				<span class="pageChangeButton" style='float:left;'>
					<a href="itemsPron?${urllib.parse.urlencode(prevPage)}">prev</a>
				</span>
			% endif
			<span class="pageChangeButton" style='float:right;'>
				<a href="itemsPron?${urllib.parse.urlencode(nextPage)}">next</a>
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