## -*- coding: utf-8 -*-
<!DOCTYPE html>


<%namespace name="tableGenerators" file="/gentable.mako"/>
<%namespace name="sideBar"         file="/gensidebar.mako"/>
<%namespace name="ut"              file="/utilities.mako"/>
<%namespace name="ap"              file="/activePlugins.mako"/>
<%namespace name="treeRender"      file="/books/render.mako"/>
<%namespace name="bookSearch"      file="/books/renderSearch.mako"/>
<%namespace name="genericFuncs"    file="/tags/genericFuncs.mako"/>

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
import traceback
import string
import nameTools as nt

import urllib.parse
%>

<%
startTime = time.time()
# print("Rendering begun")
%>



<%def name="queryError(errStr=None)">
	<br>

	<div class="errorPattern">
		<h2>Content Error!</h2>
		<p>${errStr}</p>

	</div>

</%def>


<%def name="renderItemSearch(itemNames)">


	<script type="text/javascript">

		function asyncRequest(targetUrl, replaceId)
		{
			$.get(targetUrl,
				function( response, status, xhr )
				{
					if ( status == "error" )
					{
						var msg = "Sorry but there was an error: ";
						$( "#error" ).html( msg + xhr.status + " " + xhr.statusText );
					}
					else
					{
						console.log('Output: ', replaceId)
						$('#'+replaceId).html(response);
					}
				}
			);
		};

	</script>

	% for itemName in itemNames:
		<br>
		<strong>Search results for item</strong> '${itemName}':
		<div id='delLoad-${id(itemName)}'>

			<script>

				$(document).ready(function() {
					asyncRequest('/books/renderSearch?searchTitle=${itemName|u}', 'delLoad-${id(itemName)}');

				});

			</script>
			<center><img src='/js/loading.gif' /></center>
		</div>
	% endfor
</%def>



<%def name="lookupCrosslink(title, warn=True)">
	<%
	cursor = sqlCon.cursor()
	cursor.execute("SELECT dbid, itemname FROM book_series WHERE (itemname %% %s) ORDER BY dbid ASC;", (title, ))
	rows = cursor.fetchall()
	%>


	<h2>Title Search: ${title}</h2>


	% if rows:
		<div>
			Candidate cross-links
			% for dbId, name in rows:
					<ul>
						<li><a href='/books/book-item?dbid=${dbId}'>${dbId} - ${name}</a>
					</ul>
			% endfor
		</div>
	%else:
		No Search results!
	% endif
	<br>

</%def>







<%def name="render()">
	<%

	if not "name" in request.params:
		return ut.errorDiv("No parameters in the URL request?")

	items = request.params.getall('name')
	print()
	print()
	print("book-multisearch call!")
	print(items)
	print()
	for item in items:
		lookupCrosslink(item)
	renderItemSearch(items)

	## lookupCrosslink(title)
	## renderItemSearch(searchItems)

	## dbId = ut.getUrlParam('dbid')
	## title = ut.getUrlParam('title')
	## lndbId = ut.getUrlParam('lndb')
	## if dbId:
	## 	renderForId(dbId)
	## 	return
	## elif title:
	## 	renderTitle(title)
	## 	return
	## elif lndbId:

	## 	queryError("Whoops! LNDB id lookup isn't working yet")
	## 	## try:
	## 	## 	## seriesId = int(lndbId)
	## 	## 	## renderId(seriesId)
	## 	## 	return
	## 	## except:
	## 	## 	traceback.print_exc()
	## 	## 	pass

	## 	return

	## queryError("No item ID in URL!")

	%>

</%def>


<body>


	<div>
		${sideBar.getSideBar(sqlCon)}
		<div class="maindiv">

			<div class="subdiv">
				<div class="contentdiv">
					<%
					render()

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