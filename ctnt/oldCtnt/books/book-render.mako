## -*- coding: utf-8 -*-

<%namespace name="tableGenerators" file="/gentable.mako"/>
<%namespace name="sideBar"         file="/gensidebar.mako"/>
<%namespace name="ut"              file="/utilities.mako"/>
<%namespace name="ap"              file="/activePlugins.mako"/>


<%!
import time
import datetime
from babel.dates import format_timedelta
import os.path
import settings
import string
import nameTools as nt

import urllib.parse
%>



<%def name="stripNovel(inStr)">
	<%
	if inStr.endswith("(Novel)"):
		inStr = inStr[:-len("(Novel)")]
	return inStr
	%>
</%def>

<%def name="renderRow(rowDict)">
	<%
	## dbid, itemname, itemtable, readingprogress, availprogress, ratingVal, sourceSite = rowDict

	itemname = stripNovel(rowDict['itemname'])


	## Multiply by 0.5 to convert from fixed-point int to float
	rating = nt.floatToRatingStr(rowDict['ratingVal'] * 0.5)

	reading = ''
	if rowDict['readingprogress'] >= 0:
		reading = '%s' % rowDict['readingprogress']

	available = ''
	if rowDict['availprogress'] >= 0:
		available = '%s' % rowDict['availprogress']




	mapper = {
		'books_lndb': 'LNDB',
		'MangaSeries': 'MU',
		'books_custom': 'MAN',
	}

	sources = []
	for source in rowDict['sourceSite']:
		if source in mapper:
			sources.append(mapper[source])
		else:
			sources.append(source)
	sources = ", ".join(sources)

	if available == '':
		available = None
	else:
		available = int(available)

	if reading == '':
		reading = None
	else:
		reading = int(reading)

	%>
	<tr>
		<td>${sources}</td>
		<td>${ut.makeBookIdLink(rowDict['dbid'], itemname)}</td>

		% if 'listName' in rowDict:
			<%
			list = ''
			if rowDict['listName']:
				list = rowDict['listName']
			%>
			<td>${ut.makeBookListLink(list, list)}</td>
		% endif

		<td>${rating}</td>


		## No translated files at all
		% if available == None and reading == None:
			<td></td>

		## Translated files, but not on any list.
		% elif available != None and reading == None:
			<td>${available}</td>

		## Read chapters, but nothing indicated as translated. Treat it as up-to-date
		% elif available == None and reading != None:
			<td bgcolor="${tableGenerators.attr.colours["upToDate"]}">${reading}</td>

		## If both entries are -1, the item is from the complete table, so show it's complete.
		% elif available == -1 and reading == -1:
			<td bgcolor="${tableGenerators.attr.colours["upToDate"]}">✓</td>

		## At this point, both items are valid integers, and at least one of them isn't -1
		## Therefore, if the read chapter is > -1, and also greater or equal to the current chapter, we're up-to-date
		% elif reading >= available:
			<td bgcolor="${tableGenerators.attr.colours["upToDate"]}">${reading}</td>

		## Otherwise, the chapter is out-of-date, so show that.
		% else:
			<td bgcolor="${tableGenerators.attr.colours["hasUnread"]}">${available}</td>
		% endif


		% if reading == -1:
			<td bgcolor="${tableGenerators.attr.colours["upToDate"]}">Finished</td>
		% elif reading == None:
			<td></td>
		% else:
			<td>${reading}</td>
		% endif

	</tr>
</%def>


<%def name="aggregateSourceList(sourceItems, noList=False)">
	<%

	itemNames = ['dbid', 'itemname', 'itemtable', 'readingprogress', 'availprogress', 'ratingVal', 'sourceSite', 'listName']

	## If we don't want the listName entry, pop it away
	if noList:
		itemNames.pop()

	maxItems = ['readingprogress', 'availprogress', 'ratingVal']

	ret = {}

	for data in sourceItems:
		row = dict(zip(itemNames, data))
		cleanName = stripNovel(row['itemname'])
		cleanName = nt.prepFilenameForMatching(cleanName)
		if cleanName in ret:
			ret[cleanName]['sourceSite'].add(row['sourceSite'])

			## Take the maximum value version of the reading/available/rating keys
			for key in maxItems:
				if row[key] > ret[cleanName][key]:
					ret[cleanName][key] = row[key]

			## And always use the /smaller/ dbid key.
			ret[cleanName]['dbid'] = min((row['dbid'], ret[cleanName]['dbid']))

		else:
			row['sourceSite'] = set([row['sourceSite']])

			ret[cleanName] = row

	sortRet = list(ret.values())
	sortRet.sort(key= lambda k: k['itemname'])
	return sortRet
	%>
</%def>


<%def name="renderBookList(listFilter=None)">
	<%


	if listFilter:
		srcFilter = '''WHERE book_series_list_entries.listname = %s'''
		args = (listFilter, )
	else:
		srcFilter = ''
		args = ()

	cursor = sqlCon.cursor()

	query = '''SELECT
			book_series.dbid,
			book_series.itemname,
			book_series.itemtable,
			book_series.readingprogress,
			book_series.availprogress,
			book_series.rating,
			book_series_list_entries.listname
		FROM book_series_list_entries
		INNER JOIN book_series
		ON book_series.dbid = book_series_list_entries.seriesid
		{srcFilter};'''.format(srcFilter=srcFilter)

	cursor.execute(query, args)

	seriesList = cursor.fetchall()
	seriesList = aggregateSourceList(seriesList, noList=bool(listFilter))

	%>


	<div>

		<table border="1px" class='fullwidth'>
			<tr>
					<th class="padded" width="130px">List</th>
					<th class="padded">Full Name</th>
					<th class="padded" width="60px">Rating</th>
					<th class="padded" width="70px">Latest Chapter</th>
					<th class="padded" width="70px">Read-To Chapter</th>
			</tr>

			<%
			for series in seriesList:
				renderRow(series)
			%>

		</table>

	</div>
</%def>


<%def name="renderBookAdd()">
	<br>
	<div>
		<strong>
			Add new book item:
		</strong>



		<script>

			function listChangeCallback(reqData, statusStr, jqXHR)
			{
				console.log("Ajax request succeeded");
				console.log(reqData);
				console.log(statusStr);

				var status = $.parseJSON(reqData);
				console.log(status)
				if (status.Status == "Success")
				{
					$('#list-status').html("✓");
					location.reload();
				}
				else
				{
					$('#list-status').html("✗");
					alert("ERROR!\n"+status.contents)
				}

			};
			function listChange()
			{
				$('#list-status').html("❍");

				var ret = ({});
				ret["new-custom-book"] = true;
				ret["new-name"] = $('#new-name').val();
				$.ajax("/api", {"data": ret, success: listChangeCallback});
				// alert("New value - "+ret["listName"]);
			}
		</script>


		<form action=''>
			<span>
				<input type="text" id="new-name">
				<input type="button" value='Add' onclick="listChange()">
			</span>
		</form>
	</div>
</%def>
<%def name="renderBookSeries(tableFilter=None)">
	<%


	if tableFilter:
		srcFilter = '''WHERE book_series_table_links.tablename = %s'''
		args = (tableFilter, )
	else:
		srcFilter = ''
		args = ()
	cursor = sqlCon.cursor()

	# Fetch all the book items.
	# Join in the source table name, and also the list (if any)
	# EXPLAIN ANALYZE says ~4.3 ms.
	# The INNER portion of the INNER JOIN is probably unnecessary, as
	# that row has a foreign key constraint into the table it's being
	# joined with, but whatever.
	query = '''SELECT
			book_series.dbid,
			book_series.itemname,
			book_series.itemtable,
			book_series.readingprogress,
			book_series.availprogress,
			book_series.rating,
			book_series_table_links.tablename,
			book_series_list_entries.listname
		FROM book_series
		INNER JOIN book_series_table_links
			ON book_series.itemtable = book_series_table_links.dbid
		LEFT OUTER JOIN book_series_list_entries
			ON book_series.dbid = book_series_list_entries.seriesid
		{srcFilter};'''.format(srcFilter=srcFilter)

	cursor.execute(query, args)

	seriesList = cursor.fetchall()
	seriesList = aggregateSourceList(seriesList)

	%>

	% if tableFilter == 'books_custom':
		${renderBookAdd()}
	% endif

	TODO: Add filtering stuff!

	<div>

		<table border="1px">
			<tr>
					<th class="padded" width="90">Source</th>
					<th class="padded" width="450">Full Name</th>
					<th class="padded" width="90">List</th>
					<th class="padded" width="80">Rating</th>
					<th class="padded" width="80">Read-To Chapter</th>
					<th class="padded" width="80">Latest Chapter</th>
			</tr>

			<%
			for series in seriesList:
				renderRow(series)
			%>

		</table>

	</div>
</%def>



