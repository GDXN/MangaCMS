## -*- coding: utf-8 -*-
<!DOCTYPE html>


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
			.html(title)
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
<body>


<div>
	${sideBar.getSideBar(sqlCon)}
	<div class="maindiv">

		<div class="subdiv skId">
			<div class="contentdiv">
				<h3>Manga (distinct)</h3>
				${tableGenerators.genLegendTable()}
				${tableGenerators.genMangaTable(tableKey=["sk", "cz", "mb"], distinct=True, limit=200)}
			</div>
		</div>

		<div class="subdiv fuFuId">
			<div class="contentdiv">
				<h3>Porn!</h3>
				${tableGenerators.genLegendTable(pron=True)}
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
	<li>fukkit, scrape batoto.</li>
	<li>also pururin.com</li>
	<li>pagechange buttons for porn broken in some instances. </li>
	<li>Deduper - Check that local duplicate of file found via DB still exists before deleting new downloads.</li>
	<li>add ability to sort directory by rating.</li>
	<li>Prefferentially rescan MangaUpdates series that got releases today (e.g. scan https://www.mangaupdates.com/releases.html).</li>
	<li>MangaUpdates name lookup passthrouth in nametools.</li>
	<li>Coerce directory structure to match MangaUpdates naming.</li>
	<li>Allow arbitrarily nested folders in reader.</li>
	<li>Modularize the side-bar in the manga browser, so the plugins can each provide their own lookup interface if they present the correct API (should be automatically discovered, ideally).</li>
	<li>Scrape ALL MangaUpdates metadata, and use that to group series when different sources use different naming schemes. (WIP)</li>
	<li>Automatically organize and sort directories so each series only has one directory. Aggregate multiple directories so they're named in accord with MangaUpdates
	naming approach. Note <b> this makes MangaUpdates the final authority on what to refer to series as. Deal with it</b></li>
	<li>Ability to disable bulk-downloading.</li>
	<li>Add failed item introspection table.</li>
	<li>Fix presetting of item rating field.</li>
	<li>Add planned routes to look into the various tables (can I share code across the various query mechanisms?) (Mostly complete)</li>
	<br>
</ul>
</p>
<p>
<b>Reader</b>
<ul>
	<li>reader shits itself on unicode urls.</li>
	<li>Add current page position bar when popup menus are visible.</li>
	<li>Make zoom mode a bit more intelligent (e.g. look at aspect ratio to guess zoom mode).</li>
	<li>Trigger directory cache update if a non-existent directory access is attempted</li>
</ul>
</p>

<p>

<b>Complete:</b>
<ul>
	<li><strike>Add legend key for what row colours mean (easy).</strike></li>
	<li><strike>Add better time-stamp granularity to Starkana Scraper.</strike> (I think?)</li>
	<li><strike>MangaBaby.com scraper</strike></li>
	<li><strike>Flatten any found duplicate directories, when they span more then one of the manga-folders.</strike></li>
	<li><strike>FIX NATURAL SORTING</strike></li>
	<li><strike>Make series monitoring tool for MT update periodically</strike></li>
	<li><strike>Automated tag update mechanism!</strike></li>
	<li><strike>Commit hooks to track the number of items in the mangaTable, without the massive overhead `SELECT COUNT(*)` has on SQLite (this should be fun and educational in terms of SQL).</strike></li>
	<li><strike>Generalize the image-cleaner to remove all annoying batoto/starkana/whatever images from downloaded archives. Possibly make it possible to run in batch mode? It should have a local directory of "bad" images that are scanned on start, and compare using hashes (or full on bitwise?).</strike></li>
</ul>
</p>

<%
stopTime = time.time()
timeDelta = stopTime - startTime
%>

<p>This page rendered in ${timeDelta} seconds.</p>

</body>
</html>