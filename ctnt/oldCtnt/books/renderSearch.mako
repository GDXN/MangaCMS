## -*- coding: utf-8 -*-

<%namespace name="tableGenerators" file="/gentable.mako"/>
<%namespace name="sideBar"         file="/gensidebar.mako"/>
<%namespace name="ut"              file="/utilities.mako"/>
<%namespace name="ap"              file="/activePlugins.mako"/>
<%namespace name="treeRender"      file="/books/render.mako"/>


<%!
import time
import sql
import sql.operators as sqlo
import functools
import operator as opclass

import settings

from natsort import natsorted
startTime = time.time()

bookTable = sql.Table("book_items")

bookCols = (
		bookTable.dbid,
		bookTable.src,
		bookTable.dlstate,
		bookTable.url,
		bookTable.title,
		bookTable.series,
		bookTable.istext,
		bookTable.fhash,
		bookTable.mimetype
	)


srcLookup = dict(settings.bookSources)


def buildQuery(srcTbl, cols, **kwargs):

	orOperators = []
	andOperators = []


	# Trigram similarity search uses the '%' symbol. It's only exposed by the python-sql library as the
	# "mod" operator, but the syntax is compatible.
	if 'originTrigram' in kwargs and kwargs['originTrigram']:
		andOperators.append(sqlo.Mod(srcTbl.title, kwargs['originTrigram']))


	if orOperators:
		orCond = functools.reduce(opclass.or_, orOperators)
		andOperators.append(orCond)
	if andOperators:
		where = functools.reduce(opclass.and_, andOperators)
	else:
		where=None

	query = srcTbl.select(*cols, where=where)


	return query

%>


<%def name="renderBookRow(row)">
	<%
	if row['src'] in srcLookup:
		source = srcLookup[row['src']]
	else:
		source = row['src']

	%>
	<tr>
		<td>${source}</td>
		<td><a href='/books/render?url=${row['url'] | u}'>${row['title']}</a></td>
		<td><a href='${row['url']}'>src</a></td>
	</tr>
</%def>

<%def name="genBookSearch(originTrigram=None)">

	<%

	query = buildQuery(bookTable,
		bookCols,
		originTrigram = originTrigram)


	query, params = tuple(query)
	print('query', query)
	print('params', params)

	with sqlCon.cursor() as cur:

		if " % " in query:
			query = query.replace(" % ", " %% ")
		cur.execute(query, params)
		tblCtntArr = cur.fetchall()

	rows = []
	for row in tblCtntArr:

		row = dict(zip(['dbid', 'src', 'dlstate', 'url', 'title', 'series', 'istext', 'fhash', 'mimetype'], row))
		rows.append(row)


	rows = natsorted(rows, key=lambda x: x['title'].replace("-", " "))

	%>
	% if rows:
		<table border="1px" class='fullwidth'>
			<tr>

				<th class="uncoloured" width="15%">Source</th>
				<th class="uncoloured">Title</th>
				<th class="uncoloured" width="8%">OrigLnk</th>


			</tr>

			% for row in rows:
				${renderBookRow(row)}
			% endfor

		</table>
	% else:
		<div class="errorPattern">No items!</div>
	% endif
</%def>
