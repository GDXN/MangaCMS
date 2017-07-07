## -*- coding: utf-8 -*-
<!DOCTYPE html>
<html>
<head>
	<title>WAT WAT IN THE BATT</title>
	${ut.headerBase()}
</head>

<%startTime = time.time()%>

<%namespace name="ut"              file="utilities.mako"/>
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





<%def name="getTagTable()">
	<%

	cur.execute('SELECT tags FROM HentaiItems;')
	tagRows = cur.fetchall()
	tags = {}
	tagRows = [tag for item in tagRows if item[0] != None for tag in item[0].split()]
	for item in tagRows:
		if item in tags:
			tags[item] += 1
		else:
			tags[item] = 1

	tagQuant = sum(tags.values())
	tags = [[v, k] for k, v in tags.items()]
	tags.sort(reverse=True)
	%>
	<div class="contentdiv">
		<h3>Pron Tags (by frequency)</h3>
		<p>Total Tags = ${tagQuant}</p>
		<table border="1px">
			<tr>

				<th class="uncoloured" width="200">Tag</th>
				<th class="uncoloured" width="70">Num</th>


			</tr>




		% for quantity, tag in tags:

			<tr>
				<td><a href="/itemsPron?byTag=${tag | u}">${tag}</a></td>

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

			${getTagTable()}

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