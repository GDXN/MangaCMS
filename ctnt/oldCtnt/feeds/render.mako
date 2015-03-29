## -*- coding: utf-8 -*-
<!DOCTYPE html>
<%!
import time
%>

<%namespace name="sideBar"         file="/gensidebar.mako"/>
<%namespace name="ut"              file="/utilities.mako"/>

<%def name="fetchEntries(offset, quantity)">
	<%

	cur = sqlCon.cursor()
	cur.execute('''SELECT
				dbid,
				srcname,
				feedurl,
				contenturl,
				contentid,
				title,
				author,
				tags,
				updated,
				published
			FROM
				rss_monitor
			ORDER BY published desc
			LIMIT %s
			OFFSET %s''', (quantity, offset))
	ret = cur.fetchall()

	keys = [
				'dbid',
				'srcname',
				'feedurl',
				'contenturl',
				'contentid',
				'title',
				'author',
				'tags',
				'updated',
				'published',
			]
	data = [dict(zip(keys, item)) for item in ret]


	return data

	%>
</%def>


<%def name="renderRow(rowDat)">
	<%
	title = rowDat['title']


	source = rowDat['srcname'].title()
	date = addDate = time.strftime('%y-%m-%d %H:%M', time.localtime(rowDat['published']))
	tags = rowDat['tags']
	tags = ", ".join(tags)

	%>
	<tr>
		<td>${title}</td>
		<td>${source}</td>
		<td>${tags}</td>
		<td>${date}</td>
	</tr>
</%def>

<%def name="renderTable(data)">
	<table>
		<tr>
			<th style="width: 450px; min-width: 450px;">Title</th>
			<th style="width: 60px; min-width: 60px;">Source</th>
			<th>Tags</th>
			<th style="width: 105px; min-width: 105px;">Date</th>
		</tr>
		%for entry in data:
			<%
			renderRow(entry)
			%>
		%endfor
	</table>
</%def>

<%def name="renderRss(offset=0, quantity=200)">
	Rss render call!

	<%

	dat = fetchEntries(offset, quantity)
	renderTable(dat)

	%>

</%def>


