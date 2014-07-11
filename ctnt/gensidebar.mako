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
	mbRunning,    mbRunStart,    mbLastRunDuration    = sm.getStatus(cur, "MbLoader")


	# Counting crap is now driven by commit/update/delete hooks
	ret = cur.execute('SELECT sourceSite, dlState, quantity FROM MangaItemCounts;')
	rets = cur.fetchall()

	statusDict = {}
	for srcId, state, num in rets:
		if not srcId in statusDict:
			statusDict[srcId] = {}
		statusDict[srcId][state] = num


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
		buRunState = "<b>Running</b>"
	else:
		buRunState = "Not Running"

	if mbRunning:
		mbRunState = "<b>Running</b>"
	else:
		mbRunState = "Not Running"



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
				<li><a href="/itemsManga?sourceSite=mt&distinct=True">MT</a>
				<li><a href="/itemsManga?sourceSite=sk&distinct=True">Starkana</a>
				<li><a href="/itemsManga?sourceSite=cz&distinct=True">Crazy's Manga</a>
				<li><a href="/itemsManga?sourceSite=mb&distinct=True">MangaBaby</a>
				<hr>
				<hr>
				<li><a href="/itemsPron">Pron Files</a>
				<li><a href="/itemsPron?sourceSite=djm">DjM Files</a>
				<!-- <li><a href="/tagsDjM">DjM Tags</a> -->
				<li><a href="/itemsPron?sourceSite=fu">Fu Files</a>
				<!-- <li><a href="/tagsFu">Fu Tags</a> -->
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
		<div class="statediv mbId">
			<strong>MangaBaby:</strong><br />
			${ut.timeAgo(mbRunStart)}<br />
			${mbRunState}

			<ul>
				<li>Have: ${statusDict["mb"][DNLDED]}</li>
				<li>DLing: ${statusDict["mb"][DLING]}</li>
				<li>Want: ${statusDict["mb"][QUEUED]}</li>
				<li>Failed: ${statusDict["mb"][FAILED]}</li>
			</ul>
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
		<div class="statediv buId">
			<strong>MU Mon:</strong><br />
			${ut.timeAgo(buRunStart)}<br />
			${buRunState}

		</div>
	</div>

</%def>
