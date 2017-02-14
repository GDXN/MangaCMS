## -*- coding: utf-8 -*-
<!DOCTYPE html>


<%namespace name="tableGenerators" file="/gentable.mako"/>
<%namespace name="sideBar"         file="/gensidebar.mako"/>
<%namespace name="ut"              file="/utilities.mako"/>
<%namespace name="ap"              file="/activePlugins.mako"/>

<html>
<head>
	<title>WAT WAT IN THE BATT</title>

	${ut.headerBase()}


</head>


<%!
import time
import settings
import os

%>


<%
startTime = time.time()
# print("Rendering begun")
%>


<%

def resetDownloads(table):
	print("reset", table)

	cur = sqlCon.cursor()
	cur.execute("ROLLBACK;")
	ret = cur.execute('UPDATE {} SET dlstate = 0 WHERE dlstate < 0 AND retreivaltime >= %s'.format(table), (time.time() - (60 * 60 * 24 * 7), ))
	cur.execute("COMMIT;")


if "resetManga" in request.params:
	resetDownloads("mangaItems")
if "resetHentai" in request.params:
	resetDownloads("hentaiItems")



%>

<body>


<div>
	${sideBar.getSideBar(sqlCon)}
	<div class="maindiv">

		<div class="subdiv skId">
			<div class="contentdiv">
				<h3>Debugging tools!</h3>
				<div id='mangatable'>
					<ul>
						<li><a href="/dbg/nt">NameTools State Dump</a></li>
						<li><a href="/dbg/?resetManga=True">Reset failed manga downloads from this week.</a></li>
						<li><a href="/dbg/?resetHentai=True">Reset failed Hentai downloads from this week.</a></li>
					</ul>
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
</html>