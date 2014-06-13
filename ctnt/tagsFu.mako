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




%>





<%

cur = sqlCon.cursor()

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

offset = limit * pageNo


if "tag" in request.params:
	haveTag = request.params["tag"]
else:
	haveTag = False


%>





<%def name="genFufufuTagTable()">
	<%

	cur.execute('SELECT tags FROM FufufuuItems;')
	djmItems = cur.fetchall()
	tags = {}
	djmItems = [tag for item in djmItems if item[0] != None for tag in item[0].split()]
	for item in djmItems:
		if item in tags:
			tags[item] += 1
		else:
			tags[item] = 1
	tags = [[v, k] for k, v in tags.items()]
	tags.sort(reverse=True)
	%>
	<div class="contentdiv">
		<h3>Fufufuu Tags</h3>
		<table border="1px">
			<tr>

				<th class="uncoloured" width="200">Tag</th>
				<th class="uncoloured" width="70">Num</th>


			</tr>




		% for quantity, tag in tags:

			<tr>
				<td><a href="/itemsFufufuu?byTag=${tag | u}">${tag}</a></td>

				<td>${quantity}</td>
			</tr>

		% endfor

		</table>
	</div>

</%def>

<body>

<div>

	${sideBar.getSideBar(sqlCon)}
	<div class="maindiv">

		<div class="subdiv fuFuId">

			${genFufufuTagTable()}

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