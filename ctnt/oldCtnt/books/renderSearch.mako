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

	query = srcTbl.select(*cols, order_by = sql.Desc(srcTbl.title), where=where)


	return query

%>


## {'src': 'tsuki', 'url': 'http://www.baka-tsuki.org/project/index.php?title=Talk:Baka_to_Test_to_Shoukanjuu&action=info', 'title': 'Information for "Talk:Baka to Test to Shoukanjuu"', 'dlstate': 2, 'dbid': 510721, 'istext': True, 'mimetype': 'text/html', 'series': None, 'fhash': None}

<%def name="renderBookRow(row)">
	<tr>
		<td>${srcLookup[row['src']]}</td>
		<td><a href='/books/render?url=${row['url'] | u}'>${row['title']}</a></td>
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


	%>
	% if rows:
		<table border="1px">
			<tr>

				<th class="uncoloured" width="8%">Source</th>
				<th class="uncoloured" width="25%">Title</th>


			</tr>

			% for row in rows:
				${renderBookRow(row)}
			% endfor

		</table>
	% else:
		<div class="errorPattern">No items!</div>
	% endif
</%def>
