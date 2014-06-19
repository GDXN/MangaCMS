## -*- coding: utf-8 -*-
<!DOCTYPE html>

<%namespace name="djmTable"        file="itemsDjm.mako"/>
<%namespace name="tableGenerators" file="gentable.mako"/>
<%namespace name="sideBar"         file="gensidebar.mako"/>
<%namespace name="ut"              file="utilities.mako"/>

<html>
<head>
	<title>WAT WAT IN THE BATT</title>

	${ut.headerBase()}

	<script type="text/javascript">
		$(document).ready(function() {
		// Tooltip only Text
		$('.showTT').hover(function(){
			// Hover over code
			var title = $(this).attr('title');
			$(this).data('tipText', title).removeAttr('title');
			$('<p class="tooltip"></p>')
			.text(title)
			.appendTo('body')
			.fadeIn('slow');
		}, function() {
			// Hover out code
			$(this).attr('title', $(this).data('tipText'));
			$('.tooltip').remove();
		}).mousemove(function(e) {
			var mousex = e.pageX + 20; //Get X coordinates
			var mousey = e.pageY + 10; //Get Y coordinates
			$('.tooltip')
			.css({ top: mousey, left: mousex })
		});
		});
	</script>

</head>

<%startTime = time.time()%>



<%!
import time
import datetime
from babel.dates import format_timedelta
import os.path

%>
<%

# cur = sqlCon.cursor()
# cur.execute('SELECT addDate,processing,downloaded,dlName,dlLink,baseName,dlPath,fName,isMp,newDir FROM links WHERE isMp=1 ORDER BY addDate DESC LIMIT 100;')
# mpLinks = cur.fetchall()
# cur.execute('SELECT addDate,processing,downloaded,dlName,dlLink,baseName,dlPath,fName,isMp,newDir FROM links WHERE isMp=0 ORDER BY addDate DESC LIMIT 100;')
# baseLinks = cur.fetchall()

# cur.execute('SELECT rowid,addDate,processing,downloaded,dlName,dlLink,itemTags,dlPath,fName FROM fufufuu ORDER BY addDate DESC LIMIT 50;')
# fuuLinks = cur.fetchall()

# cur.execute('SELECT rowid,addDate,processing,downloaded,dlName,contentID,itemTags,dlPath,fName,note FROM djMoe ORDER BY addDate DESC LIMIT 25;')
# djmLinks = cur.fetchall()



%>
<body>


<div>
	${sideBar.getSideBar(sqlCon)}
	<div class="maindiv">

		<div class="subdiv skId">
			<div class="contentdiv">
				<h3>Starkana</h3>
				${tableGenerators.genLegendTable()}
				${tableGenerators.genMangaTable(tableKey="sk")}
			</div>
		</div>
		<div class="subdiv czId">
			<div class="contentdiv">
				<h3>Crazy's Manga</h3>
				${tableGenerators.genLegendTable()}
				${tableGenerators.genMangaTable(tableKey="cz")}
			</div>
		</div>

		<div class="subdiv fuFuId">
			<div class="contentdiv">
				<h3>Porn!</h3>
				${tableGenerators.genLegendTable()}
				${tableGenerators.genPronTable(["fu", "djm"])}
			</div>
		</div>
## 		<div class="subdiv djMoeId">
## 			<div class="contentdiv">
## 				<h3>Doujin Moe</h3>
## 				${tableGenerators.genLegendTable()}
## 				${tableGenerators.genPronTable("djm")}
## 			</div>
## 		</div>

	</div>
</div>

<h2>
Shit to do:
</h2>
<p>
<b>General</b>
<ul>
	<li>Commit hooks to track the number of items in the mangaTable, without the massive overhead `SELECT COUNT(*)` has on SQLite (this should be fun and educational in terms of SQL).</li>
	<li>Flatten any found duplicate directories, when they span more then one of the manga-folders.</li>
	<li>Modularize the side-bar in the manga browser, so the plugins can each provide their own lookup interface if they present the correct API (should be automatically discovered, ideally).</li>
	<li>Generalize the image-cleaner to remove all annoying batoto/starkana/whatever images from downloaded archives. Possibly make it possible to run in batch mode? It should have a local directory of "bad"
	images that are scanned on start, and compare using hashes (or full on bitwise?).</li>
	<li>Scrape ALL MangaUpdates metadata, and use that to group series when different sources use different naming schemes.</li>
	<li>Automatically organize and sort directories so each series only has one directory. Aggregate multiple directories so they're named in accord with MangaUpdates
	naming approach. Note <b> this makes MangaUpdates the final authority on what to refer to series as. Deal with it</b></li>
	<li>Ability to disable bulk-downloading.</li>
	<li>Add planned routes to look into the various tables (can I share code across the various query mechanisms?) (partially complete)</li>

</ul>
</p>
<p>
<b>Reader</b>
<ul>
	<li>Add current page position bar when popup menus are visible.</li>
	<li>Make zoom mode a bit more intelligent (e.g. look at aspect ratio to guess zoom mode).</li>
	<li>Trigger directory cache update if a non-existent directory access is attempted</li>
</ul>
</p>


<%
stopTime = time.time()
timeDelta = stopTime - startTime
%>

<p>This page rendered in ${timeDelta} seconds.</p>

</body>
</html>