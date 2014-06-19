## -*- coding: utf-8 -*-
<!DOCTYPE html>
<%!
# Module level!


import datetime
from babel.dates import format_timedelta

import statusManager as sm
import nameTools as nt

FAILED = -1
QUEUED = 0
DLING  = 1
DNLDED = 2

%>

<%namespace name="ut" file="utilities.mako"/>


<%def name="getSideBar(sqlConnection)">

	<%

	cur = sqlConnection.cursor()

	skRunning,    skRunStart,    skLastRunDuration    = sm.getStatus(cur, "SkLoader")
	czRunning,    czRunStart,    czLastRunDuration    = sm.getStatus(cur, "CzLoader")
	fuRunning,    fuRunStart,    fuLastRunDuration    = sm.getStatus(cur, "Fufufuu")
	djMRunning,   djMRunStart,   djMLastRunDuration   = sm.getStatus(cur, "DjMoe")
	buRunning,    buRunStart,    buLastRunDuration    = sm.getStatus(cur, "BuMon")


	# Counting crap is now driven by commit/update/delete hooks
	ret = cur.execute('SELECT sourceSite, dlState, quantity FROM MangaItemCounts;')
	rets = cur.fetchall()

	statusDict = {}
	for srcId, state, num in rets:
		if not srcId in statusDict:
			statusDict[srcId] = {}
		statusDict[srcId][state] = num

	print("row", statusDict)


	if skRunning:
		skRunState = "<b>Running</b>"
	else:
		skRunState = "Not Running"



	if czRunning:
		czRunState = "<b>Running</b>"
	else:
		czRunState = "Not Running"



	if fuRunning:
		fuRunState = "<b>Running</b>"
	else:
		fuRunState = "Not Running"

	if djMRunning:
		djmRunState = "<b>Running</b>"
	else:
		djmRunState = "Not Running"

	if buRunning:
		buState = "<b>Running</b>"
	else:
		buState = "Not Running"



	%>

	<div class="statusdiv">
		<div class="statediv navId">
			<strong>Navigation:</strong><br />
			<ul>
				<li><a href="/">Index</a>
				<hr>
				<hr>
				<li><a href="/reader/">Manga Reader</a>
				<hr>
				<li>${ut.createReaderLink("Random Manga", nt.dirNameProxy.random())}
				<hr>
				<hr>
				<li><a href="/bmUpdates">Baka Manga</a>
				<li><a href="/dirListing">Dir Listing</a>
				<hr>
				<li><a href="/seriesMon">Series Monitor</a>
				<hr>
				<li><a href="/itemsMt?picked=True">MT Picked</a>
				<li><a href="/itemsMt?picked=False">MT Other</a>
				<li><a href="/itemsSk?distinct=True">Starkana</a>
				<li><a href="/itemsCz?distinct=True">Crazy's Manga</a>
				<hr>
				<hr>
				<li><a href="/itemsPron">Pron Files</a>
				<hr>
				<li><a href="/itemsDjm">DjM Files</a>
				<li><a href="/tagsDjM">DjM Tags</a>
				<hr>
				<li><a href="/itemsFufufuu">Fu Files</a>
				<li><a href="/tagsFu">Fu Tags</a>
				<hr>
				<hr>
				<li><a href="/dbFix">DB Tweaker</a>
			</ul>
		</div>
		<br>

		<div class="statediv">
			<strong>Status:</strong>
		</div>
		<div class="statediv skId">
			<strong>Starkana:</strong><br />
			${ut.timeAgo(skRunStart)}<br />
			${skRunState}
			<ul>
				<li>Have: ${statusDict["sk"][DNLDED]}</li>
				<li>DLing: ${statusDict["sk"][DLING]}</li>
				<li>Want: ${statusDict["sk"][QUEUED]}</li>
				<li>Failed: ${statusDict["sk"][FAILED]}</li>
			</ul>

		</div>
		<div class="statediv czId">
			<strong>Crazy's Manga:</strong><br />
			${ut.timeAgo(czRunStart)}<br />
			${czRunState}

			<ul>
				<li>Have: ${statusDict["cz"][DNLDED]}</li>
				<li>DLing: ${statusDict["cz"][DLING]}</li>
				<li>Want: ${statusDict["cz"][QUEUED]}</li>
				<li>Failed: ${statusDict["cz"][FAILED]}</li>
			</ul>
		</div>
		<div class="statediv buId">
			<strong>MU Mon:</strong><br />
			${ut.timeAgo(buRunStart)}<br />
			${buState}

		</div>
		<div class="statediv djMoeId">
			<strong>DjMoe:</strong><br />
			${ut.timeAgo(djMRunStart)}<br />
			${djmRunState}
			<ul>
				<li>Have: ${statusDict["djm"][DNLDED]}</li>
				<li>DLing: ${statusDict["djm"][DLING]}</li>
				<li>Want: ${statusDict["djm"][QUEUED]}</li>
				<li>Failed: ${statusDict["djm"][FAILED]}</li>
			</ul>

		</div>
		<div class="statediv fuFuId">
			<strong>Fufufuu:</strong><br />
			${ut.timeAgo(fuRunStart)}<br />
			${fuRunState}

			<ul>
				<li>Have: ${statusDict["fu"][DNLDED]}</li>
				<li>DLing: ${statusDict["fu"][DLING]}</li>
				<li>Want: ${statusDict["fu"][QUEUED]}</li>
				<li>Failed: ${statusDict["fu"][FAILED]}</li>
			</ul>

		</div>
	</div>

</%def>
