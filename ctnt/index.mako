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


			$.get("/fetchtable?table=manga",
				function( response, status, xhr )
				{
					if ( status == "error" )
					{
						var msg = "Sorry but there was an error: ";
						$( "#error" ).html( msg + xhr.status + " " + xhr.statusText );
					}
					else
					{
						$('#mangatable').html(response);

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
					}
				}
			);


			$.get("/fetchtable?table=pron",
				function( response, status, xhr )
				{
					if ( status == "error" )
					{
						var msg = "Sorry but there was an error: ";
						$( "#error" ).html( msg + xhr.status + " " + xhr.statusText );
					}
					else
					{
						$('#prontable').html(response);

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
					}
				}
			);

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
				<div id='mangatable'>
					<center><img src='/js/loading.gif' /></center>
				</div>
			</div>
		</div>

		<div class="subdiv fuFuId">
			<div class="contentdiv">
				<h3>Porn!</h3>
				<div id='prontable'>
					<center><img src='/js/loading.gif' /></center>
				</div>
			</div>
		</div>

	</div>
</div>

<h2>
	Shit to do:
</h2>

<b>General</b>
<ul>
select 201 to determine next page
	<li>add half star rating options</li>
	<li>h tag collation system</li>
	<li>consolidation system for h tags</li>
	<li>smart zoom mode in overlay</li>
	<li>make zoom mode pop up last longer</li>
	<li>fancy fade out when toolbars hidden?</li>
	<li>out of row colours</li>
	<li>linebreaks in long filenames in reader popup need work</li>
	<li>zoom mode indicator for smart mode in reader</li>
	<li>fit width only if oversize?</li>
	<li>Deduper - Move database interface into scanner, one interface per thread. Make each archive scan a transaction.</li>
	<li>steal code from free manga downloader?</li>
	<li>filesize in browser</li>
	<li>ability to specify MU id in directory name? [Lnnn] or sommat?</li>
	<li>way to search for non linked directories - maybe then do levenshtein search for match?</li>
	<li>import all existing files somehow</li>
	<li>rescan series on batoto</li>
	<li>do some clever set shit to check for misplaced items in directories</li>
	<li>change db table generation to use found item paths for tables in directory view.</li>
	<li>color code mangaupdates status in reader</li>
	<li>highlight chapters < 10</li>
	<li>scan times to deduper for rescanning. Also filesizes</li>
	<li>Group the smaller scanlators into a single colour-code?</li>
	<li>ability to browse by mu tags</li>
	<li>add ability to sort directory by rating.</li>
	<li>Add failed item introspection table.</li>
	<li>artist and author in filebrowser if i have it</li>
	<li>bu page opens in new window</li>
	<li>different tag for phash desuplication</li>
	<li>IRC grabber needs a transfer stall timeout.</li>
	<li>mechanism for highlighting chosen tags in table (specifically deduped in J)</li>
	<li>Modularize the side-bar in the manga browser, so the plugins can each provide their own lookup interface if they present the correct API (should be automatically discovered, ideally).</li>
	<li>Potential race-condition in deduper when two things are scanned by separate threads simultaneously. Add a global "deletion" lock to prevent accidental removal of all copies of file</li>
	<li>Prevent full base dir refresh on directory rename.</li>
	<li>prioritize downloads by rating</li>
	<li>properly show if things are one shot</li>
	<li>tagging in web interface</li>
	<li>Trigger full series download if a series is seen by a scraper, and the local directory is both found, and rated above a threshold (Done for Batoto, needs per-plugin work. Add facilities to pluginBase?)</li>
	<li>Trigger series download if on any BU list as well (partial)</li>
	<br>
</ul>
</p>

<p>
<b>Maybe in the future:</b>
<ul>
	<li>Deduper - enable the ability to check for duplicates using phash as well. (Partial - Needs ability to search by hamming distance to work properly)</li>
	<li>cover images in file browser?</li>
	<li>Ability to disable bulk-downloading.</li>
</ul>
</p>


<p>
<b>Add Scrapers for</b>

<ul>
	<li>Manga</li>
	<ul>
		<li><strike>webtoons.com</strike></li>
		<li>Tadanohito as a H source</li>
		<li>http://www.hbrowse.com/ as a H source</li>
		<li><strike>http://lonemanga.com/</strike></li>
		<li><strike>http://egscans.com/</strike> (Via IRC)</li>
		<li><strike>redhawkscans.com</strike></li>
		<li><strike>mangajoy</strike></li>
		<li><strike>http://www.cxcscans.com/</strike></li>
		<li><strike>http://desperatescanners.weebly.com/</strike> (They release on batoto)</li>
		<li><strike>imangascans</strike> (Done, as part of IRC scraper)</li>
	</ul>
	<li>Light Novels
	<ul>
		<li>Re:Translations (Note: Will mean I'll have to interface with Google Docs - Interesting challenge?)</li>
		<li><strike>Baka-Tsuki</strike></li>
		<li><strike>JapTem</strike></li>
	</ul>
</ul>
</p>

<p>
<b>Reader</b>
<ul>
	<li>Add ability to rename directories to reader</li> (res, name)
	<li>Add current page position bar when popup menus are visible.</li>
	<li>Trigger directory cache update if a non-existent directory access is attempted</li>
	<li><strike>Make zoom mode a bit more intelligent (e.g. look at aspect ratio to guess zoom mode).</strike></li>
	<li><strike>show current image info</strike></li>
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
	<li>Getsurin ni Kiri Saku</li>
	<li>Imasugu Onii-chan ni Imouto da tte Iitai!</li>
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
</ul>
<ul>
	<li>'Hero Co., Ltd.' link only working one way</li>
	<li><strike>Add testing to nametool system</strike> (Done, wasn't the problem source)</li>
	<li><strike>Everything is getting sorted into '[zion]'</strike> Fixed, it was a scraper bug. Derp</li>
</ul>
</p>
<p>

<b>Complete:</b>
<ul>
	<li><strike>reset download button in mangatable for specific key view</strike></li>
	<li><strike>filtered h isn't being properly skipped</strike></li>
	<li><strike>fix pururin page ordering already</strike> It was a sorting issue in the session system? Fuuuuuuuuuuck.</li>
	<li><strike>Migrate to new queries from tests.test-Queries</strike> Superceeded by procedural queries using server-side cursors.</li>
	<li><strike>tag/flag for when items are mirrored to mk?</strike> DlState=3 means uploaded</li>
	<li><strike>fakku is broken?</strike> Fixed</li>
	<li><strike>Load tables asynchronously from base page</strike></li>
	<li><strike>dlstate 3 not rendering right</strike></li>
	<li><strike>have vol and chap in separate columns</strike></li>
	<li><strike>key not found error resulting in HTTP 500 for bad path after rating change</strike></li>
	<li><strike>colons in seriesnames</strike> Should already be removed. Not sure what's going on</li>
	<li><strike>sorter not properly handling items with only volume number in filename (generally prepended by "volume {xxx}").</strike></li>
	<li><strike>mk uploader needs to add uploaded files to the mk downloader list so they dont get re transferred</strike> Should be done, I think?</li>
	<li><strike>7z support in archtool</strike> Added as a result of wanting to add it to the deduper. Shared code FTW.</li>
	<li><strike>figure out why bad dir-lookup matches are all defaulting to {'dirKey': 'it takes a wizard'}</strike> Someone had put "None" in the alternative names for the "It takes a Wizard" manga. Whoops?</li>
	<li><strike>Make user-agent randomize</strike> Should have something like ~32K possible configurations now.</li>
	<li><strike>import archived djm stuff?</strike></li>
	<li><strike>tie mk uploader in properly</strike></li>
	<li><strike>proxy for name lookups.</strike></li>
	<li><strike>fix lo colums?</strike></li>
	<li><strike>automover patch path in db for moved items</strike> Added `fix-dl-paths` to `cleanDb`.</li>
	<li><strike>mangajoy sometimes only fetches one image</strike> Added some delay, hopefully it'll fix things.</li>
	<li><strike>look into pu sorting issues.</strike> Stupid logic error in download delay mechanism.</li>
	<li><strike>check that new items in bu are updating properly</strike></li>
	<li><strike>djm retagger no longer running?</strike></li>
	<li><strike>Murcielago. again</strike> <strike>Hopefully fixed by forcing NFKD unicode normalization.</strike> Fuck unicode. Arrrgh.</li>
	<li><strike>mu not in sidebar</strike> Fucked up the flags at some point. Fixed.</li>
	<li><strike>tags by number for h</strike></li>
	<li><strike>Try to do something clever with sorting items in the directory viewer. Preprocess to extract vol/chapter inteligently?</strike> Simple regex implemented. I'll have to see how it pans out</li>
	<li><strike>sort bu lists contents alphabetically</strike></li>
	<li><strike>aggregation query is fucked. somehow.</strike> Fixed with procedural filtering system.</li>
	<li><strike>scan downloads, retry missing not deduped</strike> Functin added to utilities.cleanDb</li>
	<li><strike>irc defer dir search to actual download (mk too)</strike></li>
	<li><strike>push dir updating into separate thread</strike> The issue wasn't dir-updating, it was the DB loading it's cache from disk. Fixed by postgre</li>
	<li><strike>Better mechanism for chosing colours for rows. Use a calculating system, rather then requiring manual choice</strike></li>
	<li><strike>Add file existence check to tooltip in manga table</li> I'll have to see if 200 file existence checks is a problem for page-rendering time.</strike></li>
	<li><strike>Logger output coloring system</strike></li>
	<li><strike>mangacow missing last page</strike> Fucking off-by-one error</li>
	<li><strike>UNIQUE constraint on buId for mangaseries table</strike></li>
	<li><strike>Add parent-thread info to logger path for webUtilities.</strike></li>
	<li><strike>Recreate triggers to update counts on insert/delete</strike></li>
	<li><strike>make tags case-insensitive</strike> (Switch to CITEXT should do this, added .lower() to query generator anyways)</li>
	<li><strike>mu cross references all broken</strike></li>
	<li><strike>switch relevant columns to CITEXT</strike></li>
	<li><strike><b>Distinct filter not working!</b></strike></li>
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