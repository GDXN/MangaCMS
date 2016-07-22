## -*- coding: utf-8 -*-

<%namespace name="tableGenerators" file="/gentable.mako"/>
<%namespace name="sideBar"         file="/gensidebar.mako"/>
<%namespace name="ut"              file="/utilities.mako"/>
<%namespace name="ap"              file="/activePlugins.mako"/>
<%namespace name="treeRender"      file="/books/render.mako"/>
<%namespace name="bookitem"        file="/books/book-item.mako"/>

<%!
import time
import sql
import sql.operators as sqlo
import functools
import operator as opclass
import urllib.parse
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


bookWesternTable = sql.Table("book_western_items")
bookWesternCols = (
		bookWesternTable.dbid,
		bookWesternTable.src,
		bookWesternTable.dlstate,
		bookWesternTable.url,
		bookWesternTable.title,
		bookWesternTable.series,
		bookWesternTable.istext,
		bookWesternTable.fhash,
		bookWesternTable.mimetype
	)


# srcLookup = dict(settings.bookSources)


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
	netloc = urllib.parse.urlsplit(row['url']).netloc
	rowMeta = request.matchdict['page']
	if rowMeta[-1] == 'w':
		render = 'render-w'
	else:
		render = 'render'

	%>
	<tr>
		<td>${netloc}</td>
		<td><a href='/books/${render}?url=${row['url'] | u}'>${row['title']}</a></td>
		<td><a href='${row['url']}'>src</a></td>
	</tr>
</%def>

<%def name="genBookSearch(originTrigram=None)">
	<%
	genBookSearchOnTable(bookTable, bookCols, originTrigram)
	%>
</%def>

<%def name="genBookWesternSearch(originTrigram=None)">
	<%
	genBookSearchOnTable(bookWesternTable, bookWesternCols, originTrigram)

	%>

</%def>

<%def name="genBookSearchOnTable(table, cols, originTrigram=None)">

	<%

	query = buildQuery(table,
		cols,
		originTrigram = originTrigram)


	query, params = tuple(query)
	## print('query', query)
	## print('params', params)

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

				<th class="uncoloured" width="30%">Source</th>
				<th class="uncoloured">Title</th>
				<th class="uncoloured" width="7%">OrigLnk</th>


			</tr>

			% for row in rows:
				${renderBookRow(row)}
			% endfor

		</table>
	% else:
		<div class="errorPattern">No items!</div>
	% endif
</%def>

<%

	tName = ut.getUrlParam('searchTitle')
	if tName:
		tName = tName.strip()
		genBookSearch(originTrigram=tName)

	sName = ut.getUrlParam('searchSeries')
	if sName:
		sName = sName.strip()
		bookitem.getBestMatchingSeries(sName)
%>
