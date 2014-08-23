## -*- coding: utf-8 -*-
<!DOCTYPE html>


<%namespace name="tableGenerators" file="gentable.mako"/>
<%namespace name="sideBar"         file="gensidebar.mako"/>
<%namespace name="ut"              file="utilities.mako"/>
<%namespace name="ap"              file="activePlugins.mako"/>

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
				${tableGenerators.genLegendTable()}
				<%
				# print("Calling tablegen")
				%>
				${tableGenerators.genMangaTable(distinct=True, limit=200)}
			</div>
		</div>

		<div class="subdiv fuFuId">
			<div class="contentdiv">
				<h3>Porn!</h3>
				${tableGenerators.genLegendTable(pron=True)}
				${tableGenerators.genPronTable()}
			</div>
		</div>

	</div>
</div>

<h2>
Shit to do:
</h2>
<p>
<b>General</b>
<ul>
	<li><b>Distinct filter not working!</b></li>
	<li>make tags case-insensitive</li>

	<li>fix lo colums?</li>
	<li>irc defer dir search to actual download (mk too)</li>
	<li>scrape http://www.cxcscans.com/</li>
	<li>scan downloads, retry missing not deduped</li>
	<li>different tag for phash desuplication</li>
	<li>artist and author in filebrowser if i have it</li>
	<li>ability to browse by mu tags</li>
	<li>7z support in archtool</li>
	<li>check that new items in bu are updating properly</li>
	<li>tag/flag for when items are mirrored to mk?</li>
	<li>bu page opens in new window</li>
	<li>prioritize downloads by rating</li>
	<li>properly show if things are one shot</li>
	<li>cover images in file browser?</li>
	<li>mechanism for highlighting chosen tags in table (specifically deduped in J)</li>
	<li>push dir updating into separate thread</li>
	<li>Potential race-condition in deduper when two things are scanned by separate threads simultaneously. Add a global "deletion" lock to prevent accidental removal of all copies of file</li>
	<li>Better mechanism for chosing colours for rows. Use a calculating system, rather then requiring manual choice</li>
	<li>Trigger series download if on any BU list as well (partial)</li>
	<li>proxy for name lookups.</li>
	<li>Prevent full base dir refresh on directory rename.</li>
	<li>Trigger full series download if a series is seen by a scraper, and the local directory is both found, and rated above a threshold (Done for Batoto, needs per-plugin work. Add facilities to pluginBase?)</li>
	<li>Deduper - enable the ability to check for duplicates using phash as well. (Partial - Needs ability to search by hamming distance to work properly)</li>
	<li>add ability to sort directory by rating.</li>
	<li>Modularize the side-bar in the manga browser, so the plugins can each provide their own lookup interface if they present the correct API (should be automatically discovered, ideally).</li>
	<li>Ability to disable bulk-downloading.</li>
	<li>Add failed item introspection table.</li>
	<br>
</ul>
</p>


<p>
<b>Add Scrapers for</b>
<ul>
	<li>imangascans</li>
	<li>baka-tsuki/other VN translation groups?</li>
	<li>mangajoy?</li>
</ul>
</p>

<p>
<b>Reader</b>
<ul>
	<li>show current image info</li>
	<li>Add ability to rename directories to reader</li> (res, name)
	<li>Add current page position bar when popup menus are visible.</li>
	<li>Make zoom mode a bit more intelligent (e.g. look at aspect ratio to guess zoom mode).</li>
	<li>Trigger directory cache update if a non-existent directory access is attempted</li>
	<li><strike>Chapter read to from BU in item sidebar.</strike></li>
</ul>
</p>

<p>
<b>File System Organization</b>
<ul>
	<li>Coerce directory structure to match MangaUpdates naming.</li>
	<li>Scrape ALL MangaUpdates metadata, and use that to group series when different sources use different naming schemes. (WIP)</li>
	<li>Automatically organize and sort directories so each series only has one directory. Aggregate multiple directories so they're named in accord with MangaUpdates
	naming approach. Note <b> this makes MangaUpdates the final authority on what to refer to series as. Deal with it</b></li>

</ul>
</p>

<p>
<p>
<b>Nametools Issues</b>
<ul>
	<li>Everything is getting sorted into '[zion]'</li>
	<li>
	Bad MangaUpdates Links:
	<ul>
		<li>Dungeon ni Deai wo Motomeru no wa Machigatteiru Darou ka</li>
		<li>neko ane</li>
		<li>rescue me</li>
		<li>maken-ki!</li>
		<li>murcielago</li>
		<li>Keyman - The Hand of Judgement</li>
	</ul>
	</li>
	<li><strike>Add testing to nametool system</strike> (Done, wasn't the problem source)</li>
</ul>
</p>
<p>

<b>Complete:</b>
<ul>
	<li><strike>strip metainfo from links in h (artist-, scanlators-, etc)</strike> (Also added a configurable tag highlighter)</li>
	<li><strike>Defer dir updating to after page-load to prevent occational 20 second page-loads.</strike> <strike>I think this is actually the DB loading the indexes from disk. Not sure.</strike> (Hopefully fixed by move to Postgre</li>
	<li><strike>IRC scraper is broken for filenames with spaces.... Yeah....</strike></li>
	<li><strike>proper transaction system for DB (or just go to postgres)</strike> (went to postgre)</li>
	<li><strike>Fix Madokami scraper</strike></li>
	<li><strike>batoto cross verify number of images</strike> Never mind, it's not a blind exploration, it's actually using the image navigator dropdown to generate image urls.</li>
	<li><strike>Implement dir moving system already!</strike></li>
	<li><strike>total chapters not always known. Handle sanely.</strike></li>
	<li><strike>find or create only choosing dirs in picked.</strike> (Fixed a while ago)</li>
	<li><strike>irc scrapinator</strike></li>
	<li><strike>auto upload to madokami</strike></li>
	<li><strike>automate color choices for reader; fukkit just do a naive implementstion of rotation in a hsv colour space</strike></li>
	<li><strike>split item color generation into hemtai and manga to provide better control</strike></li>
	<li><strike>remove k scale from filesize readout. </strike></li>
	<li><strike>reader directory page also includes database items for series</strike></li>
	<li><strike>show reader some general luv</strike></li>
	<li><strike>fakku scraper barfs on unicode</strike> (I think it's fixed?)</li>
	<li><strike>itemsManga page isn't using activePlugins.mako</strike></li>
	<li><strike>Also the itemsPron page.</strike></li>
	<li><strike>scrape mangacow</strike></li>
	<li><strike>Non-distinct manga view is borked</strike></li>
	<li><strike>Queue whole of any new series on batoto when a rating is found that's >= "++"</strike></li>
	<li><strike>Deduper - Check that local duplicate of file found via DB still exists before deleting new downloads.</strike></li>
	<li><strike>Scrape Fakku</strike></li>
	<li><strike>optimise name cleaning.</strike> Spent some time profiling. Not worth the effort (not much room for improvement).</li>
	<li><strike>optimize optimize optimize! 1 second for home rendering.</strike> (~0.5 seconds! Woot!)</li>
	<li><strike>mangafox if they dont resize.</strike> Never mind. they took down all their Manga because licensing reasons, apparently?</li>
	<li><strike>clean ! from matching system.</strike> (Was already done)</li>
	<li><strike>split porn/nonporn again?</strike></li>
	<li><strike>Fix BU Watcher login issues.</strike> Cookies are the fucking bane of my existence.</li>
	<li><strike>Add planned routes to look into the various tables (can I share code across the various query mechanisms?) (Mostly complete)</strike>(I'm calling this complete, since I only have two table-generator calls ATM)</li>
	<li><strike>Scrape download.japanzai.com</strike></li>
	<li><strike>Fix rating change facility being broken by the new reader</strike></li>
	<li><strike>Finish reader redesign</strike></li>
	<li><strike>Fix presetting of item rating field.</strike> (Accidentally fixed, I think? Not sure how, but it's now working.)</li>
	<li><strike>reader shits itself on unicode urls.</strike></li>
	<li><strike>Allow arbitrarily nested folders in reader. (added in new reader)</strike></li>
	<li><strike>Prefferentially rescan MangaUpdates series that got releases today (e.g. scan https://www.mangaupdates.com/releases.html).</strike></li>
	<li><strike>also pururin.com</strike></li>
	<li><strike>pagechange buttons for porn broken in some instances.</strike></li>
	<li><strike>MangaUpdates name lookup passthrouth in nametools.</strike></li>
	<li><strike>fukkit, scrape batoto.</strike></li>
	<li><strike>Add legend key for what row colours mean (easy).</strike></li>
	<li><strike>Add better time-stamp granularity to Starkana Scraper.</strike> (I think?)</li>
	<li><strike>MangaBaby.com scraper</strike></li>
	<li><strike>Flatten any found duplicate directories, when they span more then one of the manga-folders.</strike></li>
	<li><strike>FIX NATURAL SORTING</strike> (Fixed upstream in the natsort package)</li>
	<li><strike>Make series monitoring tool for MT update periodically</strike></li>
	<li><strike>Automated tag update mechanism!</strike></li>
	<li><strike>Commit hooks to track the number of items in the mangaTable, without the massive overhead `SELECT COUNT(*)` has on SQLite (this should be fun and educational in terms of SQL).</strike></li>
	<li><strike>Generalize the image-cleaner to remove all annoying batoto/starkana/whatever images from downloaded archives. Possibly make it possible to run in batch mode? It should have a local directory of "bad" images that are scanned on start, and compare using hashes (or full on bitwise?).</strike></li>
	<li><strike>Scrape perveden.com</strike> Fuck them, they watermark their shit. Never mind.</li>
</ul>
</p>

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