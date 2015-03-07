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



<%def name="queryError(errStr=None)">
	<br>

	<div class="errorPattern">
		<h2>Content Error!</h2>
		<p>${errStr}</p>

	</div>

</%def>


<%def name="renderListSelector(cursor, itemId)">

	<%
	cursor.execute("""SELECT listname
					FROM book_series_lists;""")

	lists = cursor.fetchall()
	# Unpack the 1-tuples that fetchall() returns.
	lists = [list[0] for list in lists]

	cursor.execute('''SELECT listname
						FROM book_series_list_entries
						WHERE seriesId=%s''', (itemId, ))
	ret = cursor.fetchone()
	if ret:
		itemList = ret[0]
	else:
		itemList = None


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
				<option value="${list}"   ${"selected='selected''" if itemList == list else ""}>${list}</option>
			% endfor
			<option value=""   ${"selected='selected''" if itemList == None else ""}>No List</option>

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


<%def name="renderControlDiv(cursor, itemId, readingprogress, availprogress)">

	<div style="float:right">
		<%
		renderListSelector(cursor, itemId)
		renderReadTo(cursor, itemId, readingprogress, availprogress)
		%>
	</div>


</%def>

<%def name="getLndbItemInfo(cursor, title)">
	<%
		ctitle = title.replace("(Novel)", " ").strip()
		cleanedtitle = nt.prepFilenameForMatching(title)
		print("cleanedTitle: '%s'" % cleanedtitle)
		cursor.execute("""SELECT dbid, changestate, ctitle, otitle,
								vtitle, jtitle, jvtitle, series,
								pub, label, volno, author,
								illust, target, description, seriesentry,
								covers, reldate, lastchanged, lastchecked,
								firstseen, cleanedtitle
						FROM books_lndb
						WHERE cleanedtitle=%s;""", (cleanedtitle, ))
		item = cursor.fetchone()
		if not item:
			return None
		keys = [
				"dbid",
				"changestate",
				"ctitle",
				"otitle",
				"vtitle",
				"jtitle",
				"jvtitle",
				"series",
				"pub",
				"label",
				"volno",
				"author",
				"illust",
				"target",
				"description",
				"seriesentry",
				"covers",
				"reldate",
				"lastchanged",
				"lastchecked",
				"firstseen",
				"cleanedtitle"
				]
		ret = dict(zip(keys, item))
		return ret


	%>
</%def>

<%def name="getMangaUpdatesInfo(muId)">
	<%
		cursor = sqlCon.cursor()

		cursor.execute("""SELECT buid, availprogress, readingprogress, buname, bulist, butags
						FROM mangaseries

						WHERE buid=%s;""", (muId, ))
		item = cursor.fetchone()

		keys = ("muId", "currentChapter", "readChapter", "seriesName", "listName", 'tags', 'genre')
		ret = dict(zip(keys, item))
		return ret

	%>
</%def>


<%def name="renderLndbInfo(itemName)">
	<div>
		<%

		cursor = sqlCon.cursor()


		data = getLndbItemInfo(cursor, itemName)



		%>
		<strong>LNDB Info</strong>
		% if not data:
			<div>No LNDB Entry!</div>

		% else:


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
		% endif
	</div>
	<br>
</%def>

<%def name="renderMangaupdatesInfo(title)">
	<div>
		<%
		muId = nt.getMangaUpdatesId(title)
		%>
		% if muId:
			<%
			muData = getMangaUpdatesInfo(muId)
			%>
			<strong>MangaUpdates Info</strong>
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
	</div>
</%def>


<%def name="renderForId(dbId)">
	<%


	cursor = sqlCon.cursor()
	cursor.execute("SELECT dbid, itemname, itemtable, readingprogress, availprogress, rating FROM book_series WHERE dbid=%s", (dbId, ))
	row = cursor.fetchone()
	print(row)

	if not row:
		queryError("Database ID is not valid")
		return

	dbid, itemname, itemtable, readingprogress, availprogress, rating = row

	%>


	<h2>Item Title: ${itemname}</h2>

	<%

	renderControlDiv(cursor, dbid, readingprogress, availprogress)
	renderLndbInfo(itemname)
	renderMangaupdatesInfo(itemname)
	%>
</%def>

<%def name="renderTitle(title)">

	<h2>Item Title: ${title}</h2>
	<div>
		<strong>Warning: No id link, cannot edit read status.</strong>
	</div>
	<br>
	<%
	renderLndbInfo(title)
	renderMangaupdatesInfo(title)
	%>
</%def>

<%def name="render()">
	<%



	dbId = ut.getUrlParam('dbid')
	title = ut.getUrlParam('title')
	lndbId = ut.getUrlParam('lndb')
	if dbId:
		renderForId(dbId)
		return
	elif title:
		renderTitle(title)
		return
	elif lndbId:

		queryError("Whoops! LNDB id lookup isn't working yet")
		## try:
		## 	## seriesId = int(lndbId)
		## 	## renderId(seriesId)
		## 	return
		## except:
		## 	traceback.print_exc()
		## 	pass

		return

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