## -*- coding: utf-8 -*-
<!DOCTYPE html>

<%startTime = time.time()%>

<%namespace name="tableGenerators" file="gentable.mako"/>
<%namespace name="sideBar"         file="gensidebar.mako"/>
<%namespace name="ap"              file="activePlugins.mako"/>

<%namespace name="ut"              file="utilities.mako"/>



<%!
import statusManager as sm
import nameTools as nt
import time
import urllib.parse
import settings

FAILED = -1
QUEUED = 0
DLING  = 1
DNLDED = 2
%>


<%def name="renderStatus(name, cssClass, statusDict, dictKey, vals)">
	<%

	if vals:
		running, runStart, lastRunDuration, lastErr = vals
		runStart = ut.timeAgo(runStart)
	else:
		running, runStart, lastRunDuration, lastErr = False, "Never!", None, 0

	if running:
		runState = "<b>Running</b>"
	else:
		runState = "Not Running"

	errored = False
	if lastErr > (time.time() - 60*60*24): # If the last error was within the last 24 hours
		errored = ut.timeAgo(lastErr)


	%>
	<div class="${cssClass}" >
		<strong>
			${name}
		</strong><br />
		% if errored:
			<a href="/errorLog">Error ${errored} ago!</a><br />
		% endif
		${runStart}<br />
		${runState}

		% if dictKey != None:
			% if dictKey in statusDict:
				<%
				keys = [DNLDED, DLING, QUEUED, FAILED]
				pres = [key in statusDict[dictKey] for key in keys]

				%>
				% if all(pres):
					<ul>
						<li>Have: ${statusDict[dictKey][DNLDED]}</li>
						<li>DLing: ${statusDict[dictKey][DLING]}</li>
						<li>Want: ${statusDict[dictKey][QUEUED]}</li>
						<li>Failed: ${statusDict[dictKey][FAILED]}</li>
					</ul>
				% endif
			## % else:
				## <b>WARN: No lookup dict built yet!</b>
			% endif
		% endif

	</div>

</%def>

<%def name="genStatus(sqlConnection)">

	<%

	cur = sqlConnection.cursor()
	cur.execute("ROLLBACK;")

	# Counting crap is now driven by commit/update/delete hooks
	cur.execute('SELECT sourceSite, dlState, quantity FROM MangaItemCounts;')
	rets = cur.fetchall()

	statusDict = {}
	for srcId, state, num in rets:
		if not srcId in statusDict:
			statusDict[srcId] = {}
		if not state in statusDict[srcId]:
			statusDict[srcId][state] = num
		else:
			statusDict[srcId][state] += num
	try:
		randomLink = ut.createReaderLink("Random", nt.dirNameProxy.random())
	except ValueError:
		randomLink = "Not Available"



	# Counting crap is now driven by commit/update/delete hooks
	cur.execute('SELECT id, next_run_time, job_state FROM apscheduler_jobs ORDER BY id DESC;')
	sched = cur.fetchall()


	# Counting crap is now driven by commit/update/delete hooks
	cur.execute('SELECT name,running,lastRun,lastRunTime,lastError FROM pluginstatus ORDER BY name;')
	pluginList = cur.fetchall()

	allPlugins = {}
	for item in pluginList:
		allPlugins[item[0]] = item[1:]



	%>
	<div class='contentdiv'>
		<h1>Status:</h1>

		% for item in ap.attr.sidebarItemList:
			<%
			if not ut.ip_in_whitelist():
				if item['type'] == "Porn":
					continue

			if not item["renderSideBar"]:
				continue
			if not item["dbKey"]:
				continue


			vals = allPlugins.pop(item["dbKey"], False)
			print(vals)
			## vals = sm.getStatus(cur, item["dbKey"])

			renderStatus(item["name"], item['cssClass']+" statediv", statusDict, item["dictKey"], vals)

			%>
		% endfor
		<hr>
		% for key, value in allPlugins.items():
			<%
			if key.endswith("Scrape"):
				key = key[:-6]
			renderStatus(key, 'extrastatediv', statusDict, 'Nope', value)

			%>
		% endfor


		<h2>Schedule:</h2>
		<table>
			<col width="400px">
			<col width="200px">
			<col width="100px">
			% for jId, nextRun, state in sched:
				<tr>
					<td>${jId}</td>
					<td>${ut.timeAhead(nextRun)}</td>
					<td>${len(state)}</td>
				</tr>
			% endfor
		</table>
	</div>

</%def>



<html>
<head>
	<title>WAT WAT IN THE BATT</title>

	${ut.headerBase()}


	</script>

</head>


<body>


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

<div>
	${sideBar.getSideBar(sqlCon)}
	<div class="maindiv">

		<div class="subdiv skId">
		<%
		genStatus(sqlCon)
		%>

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



WAT?
