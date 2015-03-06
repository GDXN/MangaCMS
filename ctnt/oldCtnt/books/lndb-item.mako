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
import traceback
import string
import nameTools as nt

import urllib.parse
%>

<%
startTime = time.time()
# print("Rendering begun")
%>

<%def name="renderRow(rowData)">
	<h2>LNDB Book Series: </h2>
</%def>

<%def name="renderError(rowData)">
	<h2>LNDB Book Series: </h2>
</%def>



<%def name="queryError(errStr=None)">
	<br>

	<div class="errorPattern">
		<h2>Content Error!</h2>
		<p>${errStr}</p>

	</div>

</%def>


<%def name="renderListSelector(cursor, listname, itemId)">

	<%
	cursor.execute("""SELECT listname
					FROM book_series_lists;""")

	lists = cursor.fetchall()

	# Unpack the 1-tuples that fetchall() returns.
	lists = [list[0] for list in lists]

	%>


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
				alert("ERROR!\n"+status.Message)
			}

		};
		function listChange(newList)
		{
			$('#list-status').html("❍");

			var ret = ({});
			ret["set-list-for-book"] = "${itemId}";
			ret["listName"] = newList;
			$.ajax("/api", {"data": ret, success: listChangeCallback});
			// alert("New value - "+newList);
		}
	</script>

	<div class="lightRect itemInfoBox">
		List:<br>

		<select name="list" id="list" onchange="listChange(this.value)" style='width:180px;'>
			% for list in lists:
				<option value="${list}"   ${"selected='selected''" if listname == list else ""}>${list}</option>
			% endfor
			<option value=""   ${"selected='selected''" if listname == None else ""}>No List</option>

		</select>
		<span id="list-status">✓</span>
	</div>

</%def>



<%def name="renderReadTo(cursor, itemId, readingprogress, availprogress)">

	<%
	cursor.execute("""SELECT listname
					FROM book_series_lists;""")

	lists = cursor.fetchall()

	# Unpack the 1-tuples that fetchall() returns.
	lists = [list[0] for list in lists]
	print(lists)
	if availprogress < 0:
		availprogress = ' -'
	if readingprogress < 0:
		readingprogress = ' -'

	%>
	<script>


		function readToCallback	(reqData, statusStr, jqXHR)
		{
			console.log("Ajax request succeeded");
			console.log(reqData);
			console.log(statusStr);

			var status = $.parseJSON(reqData);
			console.log(status)
			if (status.Status == "Success")
			{
				$('#reading-status').html("✓");
				$('#readto').html(status.readTo);
			}
			else
			{
				$('#reading-status').html("✗");
				alert("ERROR!\n"+status.Message)
			}

		};
		function changeRating(delta)
		{
			$('#reading-status').html("❍");

			var ret = ({});
			ret["set-read-for-book"] = "${itemId}";
			ret["itemDelta"] = delta;
			$.ajax("/api", {"data": ret, success: readToCallback});
			// alert("New value - "+delta);
		}
	</script>

	<div class="lightRect itemInfoBox">
		<div>
			Read to: <span id='readto'>${readingprogress}</span><br>
			<a href="javascript:void(0)" onclick='changeRating(+10);'>+10</a>
			<a href="javascript:void(0)" onclick='changeRating(+5);'>+5</a>
			<a href="javascript:void(0)" onclick='changeRating(+1);'>+1</a>
			<a href="javascript:void(0)" onclick='changeRating(-1);'>-1</a>
			<a href="javascript:void(0)" onclick='changeRating(-5);'>-5</a>
			<a href="javascript:void(0)" onclick='changeRating(-10);'>-10</a>

		</div>
		<div>
			Available: <span id='available'>${availprogress}</span>
		</div>
		<div>
		</div>
		<span id="reading-status">✓</span>
	</div>

</%def>


<%def name="getLndbItemInfo(cursor, itemId)">
	<%
		cursor.execute("""SELECT books_lndb.dbid,
							books_lndb.changestate,
							books_lndb.ctitle,
							books_lndb.otitle,
							books_lndb.vtitle,
							books_lndb.jtitle,
							books_lndb.jvtitle,
							books_lndb.series,
							books_lndb.pub,
							books_lndb.label,
							books_lndb.volno,
							books_lndb.author,
							books_lndb.illust,
							books_lndb.target,
							books_lndb.description,
							books_lndb.seriesentry,
							books_lndb.covers,
							books_lndb.readingprogress,
							books_lndb.availprogress,
							books_lndb.rating,
							books_lndb.reldate,
							books_lndb.lastchanged,
							books_lndb.lastchecked,
							books_lndb.firstseen,
							listname
						FROM books_lndb
						LEFT JOIN book_series_series_list ON book_series_series_list.seriesId = books_lndb.dbid
						WHERE books_lndb.dbid=%s;""", (itemId, ))
		item = cursor.fetchone()

		keys = ['dbid', 'changestate', 'ctitle', 'otitle',
			'vtitle', 'jtitle', 'jvtitle', 'series',
			'pub', 'label', 'volno', 'author',
			'illust', 'target', 'description',
			'seriesentry', 'covers', 'readingprogress',
			'availprogress', 'rating', 'reldate',
			'lastchanged', 'lastchecked', 'firstseen',
			'listname']
		ret = dict(zip(keys, item))
		return ret

	%>
</%def>

<%def name="getMangaUpdatesInfo(cursor, muId)">
	<%

		cursor.execute("""SELECT buid, availprogress, readingprogress, buname, bulist, butags
						FROM mangaseries

						WHERE buid=%s;""", (muId, ))
		item = cursor.fetchone()

		keys = ("muId", "currentChapter", "readChapter", "seriesName", "listName", 'tags', 'genre')
		ret = dict(zip(keys, item))
		return ret

	%>
</%def>


<%def name="renderId(itemId)">
	<%

	cursor = sqlCon.cursor()


	data = getLndbItemInfo(cursor, itemId)


	muId = nt.getMangaUpdatesId(data['ctitle'])

	%>


	<h2>Series: ${data['ctitle']}</h2>


	<div style="float:right">
		<%
		renderListSelector(cursor, data['listname'], itemId)
		renderReadTo(cursor, itemId, data['readingprogress'], data['availprogress'])
		%>
	</div>

	<div>
		<table>

			<col width="200">
			<col width="200">
			<tr>
				<td>Series Name:</td>
				<td>${data['ctitle']}</td>
			</tr>

			<tr>
				<td>Japanese Name:</td>
				<td>${data['jtitle']}</td>
			</tr>

			<tr>
				<td>Author:</td>
				<td>${data['author']}</td>
			</tr>

			<tr>
				<td>Illustrator:</td>
				<td>${data['illust']}</td>
			</tr>
			<tr>
				<td>Target Demographic:</td>
				<td>${data['target']}</td>
			</tr>

			<tr>
				<td>Published Volumes:</td>
				<td>${data['volno']}</td>
			</tr>
		</table>
	</div>
	% if muId:
		<%
		muData = getMangaUpdatesInfo(cursor, muId)
		%>
		<h3 style='text-align:left;'>MangaUpdates Cross-Reference: ${data['ctitle']}</h3>
		## <div>
		## 	${muId}
		## 	${muData}
		## </div>
		<table>

			<col width="200">
			<col width="200">
			<tr>
				<td>Series Name:</td>
				<td>${muData['seriesName']}</td>
			</tr>

			<tr>
				<td>MU List:</td>
				<td>${muData['listName']}</td>
			</tr>


			<tr>
				<td>Read to:</td>
				<td>${muData['readChapter']}</td>
			</tr>
			<tr>
				<td>Available chapters:</td>
				<%
				avail = muData['currentChapter']
				if avail == -1 and muData['readChapter'] >= 0:
					avail = muData['readChapter']
				elif avail == -1:
					avail = None
				%>
				<td>${avail}</td>
			</tr>
			<tr>
				<td>Tags:</td>
				<td>${muData['tags']}</td>
			</tr>
		</table>

	% endif
</%def>


<%def name="render()">
	<%


	if "dbid" in request.params:
		try:
			seriesId = int(request.params["dbid"])
			renderId(seriesId)
			return
		except:
			traceback.print_exc()
			pass

	queryError("No item ID in URL!")

	%>

</%def>


<body>


	<div>
		${sideBar.getSideBar(sqlCon)}
		<div class="maindiv">

			<div class="subdiv">
				<div class="contentdiv">
					<%
					render()

					%>


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