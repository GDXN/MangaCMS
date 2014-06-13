## -*- coding: utf-8 -*-
<!DOCTYPE html>
<%!
# Module level!


import datetime
from babel.dates import format_timedelta

import statusManager as sm

%>

<%namespace name="ut" file="utilities.mako"/>


<%def name="getSideBar(sqlConnection)">

	<%

	cur = sqlConnection.cursor()

	mtRunning,    mtRunStart,    mtLastRunDuration    = sm.getStatus(cur, "MtLoader")
	mtMonRunning, mtMonRunStart, mtMonLastRunDuration = sm.getStatus(cur, "MtMonitor")
	fuRunning,    fuRunStart,    fuLastRunDuration    = sm.getStatus(cur, "Fufufuu")
	djMRunning,   djMRunStart,   djMLastRunDuration   = sm.getStatus(cur, "DjMoe")
	buRunning,    buRunStart,    buLastRunDuration    = sm.getStatus(cur, "BuMon")



	if mtRunning:
		mtRunState = "<b>Running</b>"
	else:
		mtRunState = "Not Running"


	if mtMonRunning:
		mtMonRunState = "<b>Running</b>"
	else:
		mtMonRunState = "Not Running"


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

	cur.execute('SELECT COUNT(*) FROM MangaItems WHERE dlState=2 AND flags LIKE "%picked%";')
	mpItems = cur.fetchone()[0]
	cur.execute('SELECT COUNT(*) FROM MangaItems WHERE dlState=0 AND flags LIKE "%picked%";')
	mpNewItems = cur.fetchone()[0]
	cur.execute('SELECT COUNT(*) FROM MangaItems WHERE dlState=2 AND NOT flags LIKE "%picked%";')
	baseItems = cur.fetchone()[0]
	cur.execute('SELECT COUNT(*) FROM MangaItems WHERE dlState=0 AND NOT flags LIKE "%picked%";')
	baseNewItems = cur.fetchone()[0]
	cur.execute('SELECT COUNT(*) FROM MangaItems WHERE dlState=1;')
	mtWorkItems = cur.fetchone()[0]


	cur.execute('SELECT COUNT(*) FROM MangaSeries;')
	mtMonItems = cur.fetchall()[0][0]
	# mtMonItems = "<marquee><b>FIXME</b></marquee>"

	cur.execute('SELECT COUNT(*) FROM FufufuuItems WHERE dlState=2;')
	fuItems = cur.fetchone()[0]
	cur.execute('SELECT COUNT(*) FROM FufufuuItems WHERE dlState=1;')
	fuWorkItems = cur.fetchone()[0]
	cur.execute('SELECT COUNT(*) FROM FufufuuItems WHERE dlState=0;')
	fuNewItems = cur.fetchone()[0]

	cur.execute('SELECT COUNT(*) FROM DoujinMoeItems WHERE dlState=2;')
	djmItems = cur.fetchone()[0]
	cur.execute('SELECT COUNT(*) FROM DoujinMoeItems WHERE dlState=1;')
	djmWorkItems = cur.fetchone()[0]
	cur.execute('SELECT COUNT(*) FROM DoujinMoeItems WHERE dlState=0;')
	djmNewItems = cur.fetchone()[0]


	%>

	<div class="statusdiv">
		<div class="statediv navId">
			<strong>Navigation:</strong><br />
			<ul>
				<li><a href="/">Index</a>
				<hr>
				<li><a href="/bmUpdates">Baka Manga</a>
				<li><a href="/dirListing">Dir Listing</a>
				<hr>
				<li><a href="/seriesMon">Series Monitor</a>
				<hr>
				<li><a href="/itemsMt?picked=True">MT Picked</a>
				<li><a href="/itemsMt?picked=False">MT Other</a>
				<hr>
				<li><a href="/itemsDjm">DjM Files</a>
				<li><a href="/tagsDjM">DjM Tags</a>
				<hr>
				<li><a href="/itemsFufufuu">Fu Files</a>
				<li><a href="/tagsFu">Fu Tags</a>
				<hr>
				<li><a href="/dbFix">DB Tweaker</a>
				<hr>
				<li><a href="/reader/">Manga Reader</a>
			</ul>
		</div>
		<br>

		<div class="statediv">
			<strong>Status:</strong>
		</div>
		<div class="statediv mtMainId">
			<strong>MT:</strong><br />
			${ut.timeAgo(mtRunStart)}<br />
			${mtRunState}
			<hr>
			Picked:
			<ul>
				<li>Have: ${mpItems}</li>
				<li>Want: ${mpNewItems}</li>
			</ul>
			Other:
			<ul>
				<li>Have: ${baseItems}</li>
				<li>Want: ${baseNewItems}</li>
			</ul>

			<hr>

			<ul>
				<li>DLing: ${mtWorkItems}</li>
			</ul>

		</div>
		<div class="statediv mtMonId">
			<strong>MT Monitor:</strong><br />
			${ut.timeAgo(mtMonRunStart)}<br />
			${mtMonRunState}
			<ul>
				<li>Have: ${mtMonItems}</li>
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
				<li>Have: ${djmItems}</li>
				<li>DLing: ${djmWorkItems}</li>
				<li>Want: ${djmNewItems}</li>
			</ul>
		</div>
		<div class="statediv fuFuId">
			<strong>Fufufuu:</strong><br />
			${ut.timeAgo(fuRunStart)}<br />
			${fuRunState}

			<ul>
				<li>Have: ${fuItems}</li>
				<li>DLing: ${fuWorkItems}</li>
				<li>Want: ${fuNewItems}</li>
			</ul>
		</div>
	</div>

</%def>
