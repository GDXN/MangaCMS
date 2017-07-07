## -*- coding: utf-8 -*-
<!DOCTYPE html>

<%namespace name="sideBar"         file="gensidebar.mako"/>
<%namespace name="ut"              file="utilities.mako"/>
<%namespace name="ap"              file="activePlugins.mako"/>
<%namespace name="tableGenerators" file="gentable.mako"/>

<html>
<head>
	<title>WAT WAT IN THE BATT</title>

	${ut.headerBase()}

	<script type="text/javascript">
		$(document).ready(function() {


			$.get("/fetchtable?table=manga",
				function( response, status, xhr )
				{
					if ( status == "error" )
					{
						var msg = "Sorry but there was an error: ";
						$( "#error" ).html( msg + xhr.status + " " + xhr.statusText );
					}
					else
					{
						$('#mangatable').html(response);

						${ut.mouseOverJs(key="showTT")}
					}
				}
			);


			$.get("/fetchtable?table=pron",
				function( response, status, xhr )
				{
					if ( status == "error" )
					{
						var msg = "Sorry but there was an error: ";
						$( "#error" ).html( msg + xhr.status + " " + xhr.statusText );
					}
					else
					{
						$('#prontable').html(response);

						${ut.mouseOverJs(key="showHT")}
					}
				}
			);

		});
	</script>

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


%>

<body>


<div>
	${sideBar.getSideBar(sqlCon)}
	<div class="maindiv">

		<div class="subdiv skId">
			<div class="contentdiv">
				<h3>Manga (distinct)</h3>
				<div id='mangatable'>
					<center><img src='/js/loading.gif' /></center>
				</div>
			</div>
		</div>

		% if ut.ip_in_whitelist():
			<div class="subdiv fuFuId">
				<div class="contentdiv">
					<h3>Porn!</h3>
					<div id='prontable'>
						<center><img src='/js/loading.gif' /></center>
					</div>
				</div>
			</div>
		% endif

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