## -*- coding: utf-8 -*-
<!DOCTYPE html>
<%!
# Module level!


import datetime
from babel.dates import format_timedelta

import statusManager as sm
import nameTools as nt

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


	# Counting stuff


	# 'SELECT COUNT(*) FROM MangaItems WHERE dlState=2 AND flags LIKE "%picked%";'
	# 'SELECT COUNT(*) FROM MangaItems WHERE dlState=0 AND flags LIKE "%picked%";'
	# 'SELECT COUNT(*) FROM MangaItems WHERE dlState=2 AND NOT flags LIKE "%picked%";'
	# 'SELECT COUNT(*) FROM MangaItems WHERE dlState=0 AND NOT flags LIKE "%picked%";'
	# 'SELECT COUNT(*) FROM MangaItems WHERE dlState=1;'
	# 'SELECT COUNT(*) FROM MangaSeries;'
	# 'SELECT COUNT(*) FROM FufufuuItems WHERE dlState=2;'
	# 'SELECT COUNT(*) FROM FufufuuItems WHERE dlState=1;'
	# 'SELECT COUNT(*) FROM FufufuuItems WHERE dlState=0;'
	# 'SELECT COUNT(*) FROM DoujinMoeItems WHERE dlState=2;'
	# 'SELECT COUNT(*) FROM DoujinMoeItems WHERE dlState=1;'
	# 'SELECT COUNT(*) FROM DoujinMoeItems WHERE dlState=0;'

	# cur.execute('SELECT COUNT(*) FROM AllMangaItems WHERE dlState=2 AND sourceSite="sk";')
	# skItems = cur.fetchone()[0]
	# cur.execute('SELECT COUNT(*) FROM AllMangaItems WHERE dlState=0 AND sourceSite="sk";')
	# skNewItems = cur.fetchone()[0]
	# cur.execute('SELECT COUNT(*) FROM AllMangaItems WHERE dlState=1 AND sourceSite="sk";')
	# skWorkItems = cur.fetchone()[0]


	# cur.execute('SELECT COUNT(*) FROM AllMangaItems WHERE dlState=2 AND sourceSite="cz";')
	# czItems = cur.fetchone()[0]
	# cur.execute('SELECT COUNT(*) FROM AllMangaItems WHERE dlState=0 AND sourceSite="cz";')
	# czNewItems = cur.fetchone()[0]
	# cur.execute('SELECT COUNT(*) FROM AllMangaItems WHERE dlState=1 AND sourceSite="cz";')
	# czWorkItems = cur.fetchone()[0]



	# cur.execute('SELECT COUNT(*) FROM MangaSeries;')
	# mtMonItems = cur.fetchall()[0][0]

	cur.execute('SELECT COUNT(*) FROM AllMangaItems WHERE dlState=2 AND sourceSite="fu";')
	fuItems = cur.fetchone()[0]
	cur.execute('SELECT COUNT(*) FROM AllMangaItems WHERE dlState=1 AND sourceSite="fu";')
	fuWorkItems = cur.fetchone()[0]
	cur.execute('SELECT COUNT(*) FROM AllMangaItems WHERE dlState=0 AND sourceSite="fu";')
	fuNewItems = cur.fetchone()[0]

	# cur.execute('SELECT COUNT(*) FROM AllMangaItems WHERE dlState=2 AND sourceSite="djm";')
	# djmItems = cur.fetchone()[0]
	# cur.execute('SELECT COUNT(*) FROM AllMangaItems WHERE dlState=1 AND sourceSite="djm";')
	# djmWorkItems = cur.fetchone()[0]
	# cur.execute('SELECT COUNT(*) FROM AllMangaItems WHERE dlState=0 AND sourceSite="djm";')
	# djmNewItems = cur.fetchone()[0]
	#		<ul>
	#			<li>Have: ${skItems}</li>
	#			<li>DLing: ${skWorkItems}</li>
	#			<li>Want: ${skNewItems}</li>
	#		</ul>
	#		<ul>
	#			<li>Have: ${czItems}</li>
	#			<li>DLing: ${czWorkItems}</li>
	#			<li>Want: ${czNewItems}</li>
	#		</ul>
	#		<ul>
	#			<li>Have: ${djmItems}</li>
	#			<li>DLing: ${djmWorkItems}</li>
	#			<li>Want: ${djmNewItems}</li>
	#		</ul>
	#		<ul>
	#			<li>Have: ${fuItems}</li>
	#			<li>DLing: ${fuWorkItems}</li>
	#			<li>Want: ${fuNewItems}</li>
	#		</ul>

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


		</div>
		<div class="statediv czId">
			<strong>Crazy's Manga:</strong><br />
			${ut.timeAgo(czRunStart)}<br />
			${czRunState}


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


		</div>
		<div class="statediv fuFuId">
			<strong>Fufufuu:</strong><br />
			${ut.timeAgo(fuRunStart)}<br />
			${fuRunState}


		</div>
	</div>

</%def>
