## -*- coding: utf-8 -*-
<!DOCTYPE html>

<%startTime = time.time()%>
<%namespace name="tableGenerators" file="gentable.mako"/>
<%namespace name="sideBar" file="gensidebar.mako"/>

<html>
<head>
	<title>WAT WAT IN THE BATT</title>
	<link rel="stylesheet" href="style.css">

</head>

<%!
# Module level!
import time
import datetime
from babel.dates import format_timedelta
import os.path

from operator import itemgetter

import nameTools as nt
import unicodedata




colours = {
	# Download Status
	"hasUnread"       : "FF9999",
	"upToDate"        : "99FF99",
	"notInMT"         : "9999FF",


	"failed"          : "000000",
	"moved"           : "FFFF99",
	"queued"          : "FF77FF",
	"created-dir"     : "FFE4B2",
	"not checked"     : "FFFFFF",

	# Categories

	"valid category"  : "FFFFFF",
	"bad category"    : "999999"}


%>





<%

filterStr = "/MP/"

if "filter" in request.params:
	filterStr = request.params["filter"]


%>

<body>

<div>

	${sideBar.getSideBar(sqlCon)}
	<div class="maindiv">

		<div class="subdiv buMonId" style="padding: 5px;">
			<h4>Directory Names</h4>

			<form>
				Filter items by string:
				<div style="display: inline-block;">
					<input type="text" name="filter", value="" size=50>
					<input type="submit" value="Add">
				</div>
			</form>
			Shortcuts:
			<a href="dirListing?filter=/MP/">Only in MP</a></li>
			<a href="dirListing?filter=/MN/">Only in MN</a></li>
			<a href="dirListing?filter=/Manga/">Only in Manga</a></li>
			<%
			dirDicts = nt.dirNameProxy.getDirDicts()

			dirKeys = list(dirDicts.keys())
			dirKeys.sort()

			%>
			% for key in dirKeys:
				<div>
					<hr>
					<h3>${nt.dirNameProxy.getPathByKey(key)["dir"]}</h3>
					${genDirTable(dirDicts[key])}
				</div>
			% endfor
		</div>

	</div>
<div>



<%def name="genDirTable(dirDict)">

	<table border="1px">
		<tr>
				<th class="padded" width="250">Dir Lookup Key</th>
				<th class="padded" width="650">Dir Info</th>
		</tr>
		<%

		%>
		% for key, dataDict in dirDict.items():
			<%
			if filterStr and not filterStr in dataDict:
				continue

			dictStr = "%s" % dataDict
			dictStr = nt.dirNameProxy[key]
			%>
			<tr>
				<td class="padded">'${key}'</td>
				<td class="padded">
					<table>

					% for key, value in dictStr.items():
						<% if key == "rating": continue %>
						<%
							if key == "dirKey" and dictStr["inKey"] == dictStr["dirKey"]:
								key = "dirKey, inKey"
							if key == "inKey" and dictStr["inKey"] == dictStr["dirKey"]:
								continue
						%>
						<tr>
							<td class="unpadded" width=95>${key}</td>
							<td class="unpadded" width=500>${value}</td>
						</tr>
					% endfor
					</table>
				</td>
				<!-- <td class="padded">${dictStr}</td> -->

			</tr>
		% endfor

	</table>
</%def>



<%
stopTime = time.time()
timeDelta = stopTime - startTime
%>

<p>This page rendered in ${timeDelta} seconds.</p>

</body>
</html>