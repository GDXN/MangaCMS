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

<%
mimetype, fsPath, itemUrl, distance, dbid = extradat

%>
<body>

<div>
	${sideBar.getSideBar(sqlCon)}
	<div class="maindiv">

		<div class="subdiv">
			<div class="contentdiv">
				<div>
					<h3>Item was found in the book item database, but it seems to have no
					mime-type, which means it has probably not been retreived yet.</h3>

				</div>
				<div>
					<a href='${itemUrl}'>Try to retreive from original source</a>
				</div>
				<div>
					Request Parameters: ${request.params}<br>
					Item crawl distance: ${distance} (<a href='#' onclick='resetCrawl()'>Zero distance to force fetch</a>).
				</div>

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
<script>



	function ajaxCallback(reqData, statusStr, jqXHR)
	{
		console.log("Ajax request succeeded");
		console.log(reqData);
		console.log(statusStr);

		var status = $.parseJSON(reqData);
		console.log(status)
		if (status.Status == "Success")
		{
			location.reload();
		}
		else
		{
			alert("ERROR!\n"+status.Message)
		}

	};
	function resetCrawl()
	{

		var params = ({});
		params["reset-book-crawl-dist"] = "${dbid}";
		params["western"]               = false;
		$.ajax("/api", {"data": params, success: ajaxCallback});
		// alert("New value - "+newRating);
	}
</script>

</html>



