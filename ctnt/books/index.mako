## -*- coding: utf-8 -*-
<!DOCTYPE html>


<%namespace name="tableGenerators" file="/gentable.mako"/>
<%namespace name="sideBar"         file="/gensidebar.mako"/>
<%namespace name="ut"              file="/utilities.mako"/>
<%namespace name="ap"              file="/activePlugins.mako"/>
<%namespace name="treeRender"      file="/books/render.mako"/>

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

	<link rel="stylesheet" href="/books/treeview.css">

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
import string

import urllib.parse
%>

<%def name="renderTreeRoot(rootKey, rootTitle)">
	<%


	ret = {}
	for char in string.ascii_letters + string.digits:
		cursor.execute("SELECT dbid FROM book_items WHERE title LIKE %s AND src=%s LIMIT 1;", ('{char}%'.format(char=char), rootKey))
		ret[char] = cursor.fetchone()


	for key in string.ascii_lowercase:
		if ret[key]:
			ret[key.upper()] = ret[key]
			del(ret[key])
	have = list(set([key.upper() for key, val in ret.items() if val ]))
	have.sort()



	curBase = 'item-%s' % int(time.time()*1000)

	childNum = 0
	# print(trie)

	%>

	<ul>

		<li><input type="checkbox" id="${curBase}" checked="checked" /><label for="${curBase}">${rootTitle}</label>
			<ul>
				% for key in have:
					<li>
					${treeRender.lazyTreeNode(rootKey, key)}
					</li>
				% endfor
			</ul>
		</li>
	</ul>
</%def>


<body>


<div>
	${sideBar.getSideBar(sqlCon)}
	<div class="maindiv">

		<div class="subdiv">
			<div class="contentdiv">
				<h2>BookTrie!</h2>
				<%
				cursor = sqlCon.cursor()

				# cursor.execute("SELECT url, dbid, title FROM book_items WHERE mimetype = %s ORDER BY title;", ('text/html', ))
				# ret = cursor.fetchall()

				# items = []
				# for item in ret:
				# 	filter = item[2].lower()
				# 	if filter.startswith("template:") or filter.startswith("talk:") or filter.startswith("ирис"):
				# 		continue


				# 	items.append(item)


				# trie = build_trie(items, lambda x: x[2])

				%>


				<div class="css-treeview">
					${renderTreeRoot('tsuki', 'Baka-Tsuki')}
				</div>
				<hr>
				<div class="css-treeview">
					${renderTreeRoot('japtem', 'JapTem')}
				</div>
			</div>

		</div>
	</div>
</div>


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