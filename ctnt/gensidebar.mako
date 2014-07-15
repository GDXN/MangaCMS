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

	# TURN THIS SHIT INTO A LOOP BEFORE YOU GO INSANE!


	# Counting crap is now driven by commit/update/delete hooks
	ret = cur.execute('SELECT sourceSite, dlState, quantity FROM MangaItemCounts;')
	rets = cur.fetchall()

	statusDict = {}
	for srcId, state, num in rets:
		if not srcId in statusDict:
			statusDict[srcId] = {}
		statusDict[srcId][state] = num

	sidebarItemList = [
			["SkLoader", "Starkana:",      "sk", "skId"   ],
			["CzLoader", "Crazy's Manga:", "cz", "czId"   ],
			["MbLoader", "MangaBaby:",     "mb", "fuFuId" ],
			["BtLoader", "Batoto:",        "bt", "puId" ],
			["JzLoader", "Japanzai:",      "jz", "jzId" ],
			["BuMon",    "MU Mon:",        None, "djMoeId"],
			["DjMoe",    "DjMoe:",         "djm","btId"   ],
			["Pururin",  "Pururin:",       "pu", "buId"   ],
			["Fufufuu",  "Fufufuu:",       "fu", "mbId"   ]
		]


	%>

	<div class="statusdiv">
		<div class="statediv navId">
			<strong>Navigation:</strong><br />
			<ul>
				<li><a href="/">Index</a>
				<hr>
				<hr>
				<li><a href="/reader2/browse/">Manga Reader</a>
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

		% for dbKey, title, dictKey, cssClass in sidebarItemList:
			<%
			running, runStart, skLastRunDuration = sm.getStatus(cur, dbKey)

			if running:
				runState = "<b>Running</b>"
			else:
				runState = "Not Running"
			%>
			<div class="statediv ${cssClass}">
				<strong>${title}</strong><br />
				${ut.timeAgo(runStart)}<br />
				${runState}
				% if dictKey:
					<ul>
						<li>Have: ${statusDict[dictKey][DNLDED]}</li>
						<li>DLing: ${statusDict[dictKey][DLING]}</li>
						<li>Want: ${statusDict[dictKey][QUEUED]}</li>
						<li>Failed: ${statusDict[dictKey][FAILED]}</li>
					</ul>
				% endif
			</div>
		% endfor
	</div>

</%def>
