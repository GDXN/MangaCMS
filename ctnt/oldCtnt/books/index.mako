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
	for char in string.punctuation + string.whitespace + string.ascii_letters + string.digits:

		# Escape the postgresql special chars in the like search.
		if char == "_" or char == "%":
			char = r"\\"+char

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
				%>

				% for srcKey, srcName in settings.bookSources:
					<div class="css-treeview">
						${renderTreeRoot(srcKey, srcName)}
					</div>
					<hr>
				% endfor

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