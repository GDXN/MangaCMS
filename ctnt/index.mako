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

		<div class="subdiv fuFuId">
			<div class="contentdiv">
				<h3>Fufufuu</h3>
				${tableGenerators.genLegendTable()}
				${tableGenerators.genFuuTable(tagsFilter=["english"])}
			</div>
		</div>
		<div class="subdiv djMoeId">
			<div class="contentdiv">
				<h3>Doujin Moe</h3>
				${tableGenerators.genLegendTable()}
				${tableGenerators.genDjmTable()}
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
	<li>Add planned routes to look into the various tables (can I share code across the various query mechanisms?)</li>
	<li>Make series monitoring tool for MT update periodically</li>
	<li><marquee Width=500>Get around to adding automated tag update mechanism!</marquee></li>
</ul>
</p>
<p>
<b>Reader</b>
<ul>
	<li>Add current page position bar when popup menus are visible.</li>
	<li>Make zoom mode a bit more intelligent (e.g. look at aspect ratio to guess zoom mode).</li>
	<li>Make the zoom mode change button region actually work on WinRT</li>
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