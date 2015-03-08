## -*- coding: utf-8 -*-
<!DOCTYPE html>


<%namespace name="tableGenerators" file="/gentable.mako"/>
<%namespace name="sideBar"         file="/gensidebar.mako"/>
<%namespace name="ut"              file="/utilities.mako"/>
<%namespace name="ap"              file="/activePlugins.mako"/>
<%namespace name="treeRender"      file="/books/render.mako"/>
<%namespace name="bookSearch"      file="/books/renderSearch.mako"/>
<%namespace name="genericFuncs"    file="/tags/genericFuncs.mako"/>

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
	## print(lists)
	if availprogress < 0:
		availprogress = ' -'
	if readingprogress < 0:
		readingprogress = ' -'

	%>
	<script>


		function readToCallback(reqData, statusStr, jqXHR)
		{
			console.log("Ajax request succeeded");
			console.log(reqData);
			console.log(statusStr);

			var status = $.parseJSON(reqData);
			console.log('Status value: '+status.Status)
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

<%def name="renderDeleteControl(cursor, itemId, srcTableId)">

	<%
	cursor.execute("""SELECT dbid, tablename
					FROM book_series_table_links;""")

	tables = cursor.fetchall()

	# Unpack the 1-tuples that fetchall() returns.
	lut = {}
	## print(tables)
	for tableId, tableName in tables:
		lut[tableId] = tableName


	deleteableTable = 'books_custom'

	if lut[srcTableId] != deleteableTable:
		return

	%>

	<script>

		function itemDeletedCallback(reqData, statusStr, jqXHR)
		{
			console.log("Ajax request succeeded");
			console.log(reqData);
			console.log(statusStr);

			var status = $.parseJSON(reqData);
			console.log(status)
			if (status.Status == "Success")
			{
				window.location.replace("/books/book-sources?src=books_custom")
			}
			else
			{
				alert("ERROR!\n"+status.Message)
			}

		};
		function deleteBookItem(newList)
		{


			var ret = ({});
			ret["delete-custom-book"] = true;
			ret["delete-id"] = ${itemId};

			var confirm = window.confirm("Are you sure you want to delete this item?");

			if (confirm == true)
			{
				$.ajax("/api", {"data": ret, success: itemDeletedCallback});
			}

		}
	</script>

	<div class="lightRect itemInfoBox">
		Delete custom book:
		<button onclick="deleteBookItem()">Delete</button>
	</div>
</%def>


<%def name="renderItemRatingControl(cursor, itemId, rating)">
	<%
	ratings = [
		(-1,       "-"),
		(0,         ""),
		(0.5,      "~"),
		(1,        "+"),
		(1.5,     "+~"),
		(2,       "++"),
		(2.5,    "++~"),
		(3,      "+++"),
		(3.5,   "+++~"),
		(4,     "++++"),
		(4.5,  "++++~"),
		(5,    "+++++"),
		(5.5, "+++++~"),
	]
	%>
	<script>

		function ratingChangeCallback(reqData, statusStr, jqXHR)
		{
			console.log("Ajax request succeeded");
			console.log(reqData);
			console.log(statusStr);

			var status = $.parseJSON(reqData);
			console.log(status)
			if (status.Status == "Success")
			{
				$('#rating-status').html("✓");
				console.log("Succeeded!");
				// location.reload();
			}
			else
			{
				$('#rating-status').html("✗");
				alert("ERROR!\n"+status.Message)
			}

		};
		function ratingChange(newList)
		{
			$('#rating-status').html("❍");

			var ret = ({});
			ret["set-rating-for-book"] = "${itemId}";
			ret["rating"] = newList;
			$.ajax("/api", {"data": ret, success: ratingChangeCallback});
			// alert("New value - "+newList);
		}
	</script>


	<div class="lightRect itemInfoBox">
		Item Rating:<br>

		<select name="list" id="list" onchange="ratingChange(this.value)" style='width:180px;'>
			% for value, literal in ratings:
				<option value="${value}"   ${"selected='selected''" if value == rating else ""}>${literal}</option>
			% endfor

		</select>
		<span id="rating-status">✓</span>
	</div>

</%def>

<%def name="renderControlDiv(cursor, itemId, readingprogress, availprogress, rating, srcTableId)">

	<div style="float:right">
		<%
		renderListSelector(cursor, itemId)
		renderItemRatingControl(cursor, itemId, rating)
		renderReadTo(cursor, itemId, readingprogress, availprogress)
		renderDeleteControl(cursor, itemId, srcTableId)
		%>
	</div>


</%def>

<%def name="getLndbItemInfo(cursor, title)">
	<%

		if title.endswith("(Novel)"):
			title = title[:-len("(Novel)")]

		cleanedtitle = nt.prepFilenameForMatching(title)
		## print("cleanedTitle: '%s'" % cleanedtitle)
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

		cursor.execute("""SELECT buid, availprogress, readingprogress, buname, bulist, butags, bugenre, budescription
						FROM mangaseries

						WHERE buid=%s;""", (muId, ))
		item = cursor.fetchone()

		keys = ("muId", "currentChapter", "readChapter", "seriesName", "listName", 'tags', 'genre', 'description')
		ret = dict(zip(keys, item))
		return ret

	%>
</%def>

<%def name="renderItemSearch(itemName)">
	<br>
	<strong>Search results for item</strong>
	<%


	if itemName.endswith("(Novel)"):
		itemName = itemName[:-len("(Novel)")]
	bookSearch.genBookSearch(originTrigram=itemName)
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

					<col width="200px">
					<col width="400px">
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

		<strong>MangaUpdates Info</strong>

		<%
		muId = nt.getMangaUpdatesId(title)
		%>
		% if muId:
			<%
			muData = getMangaUpdatesInfo(muId)
			%>
			## <div>
			## 	${muId}
			## 	${muData}
			## </div>
			<table>

				<col width="200px">
				<col width="400px">
				<tr>
					<td>Series Name:</td>
					<td>${ut.idToLink(muId, muData['seriesName'])}</td>
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
					<td>Genre:</td>
					<td>
						<ul>
							<%
							if not muData['genre']:
								muData['genre'] = ""

							genre = muData['genre'].split(" ")
							genre.sort()
							%>
							% for item in genre:
								<li>${genericFuncs.makeGenreLink(item, '&showonlyexists=all')}</li>
							% endfor
						</ul>
					</td>
				</tr>
				<tr>
					<td>Tags:</td>
					<td>
						<ul>
							<%
							if not muData['tags']:
								muData['tags'] = ""

							tags = muData['tags'].split(" ")
							tags.sort()
							%>
							% for item in tags:
								<li>${genericFuncs.makeTagLink(item, '&showonlyexists=all')}</li>
							% endfor
						</ul>


					</td>
				</tr>

				<tr>
					<td>MU Description:</td>
					<td>${muData['description']}</td>
				</tr>

				<tr>
					<td>MU ID:</td>
					<td>${muId}</td>
				</tr>

			</table>

		% else:
			<div>No MangaUpdates Entry!</div>
		% endif
	</div>
</%def>


<%def name="renderForId(dbId)">
	<%


	cursor = sqlCon.cursor()
	cursor.execute("SELECT dbid, itemname, itemtable, readingprogress, availprogress, rating FROM book_series WHERE dbid=%s", (dbId, ))
	row = cursor.fetchone()


	if not row:
		queryError("Database ID is not valid")
		return

	dbid, itemname, srcTableId, readingprogress, availprogress, rating = row

	## Convert fixed point rating to float
	rating = rating * 0.5

	%>


	<h2>Item Title: ${itemname}</h2>

	<%

	renderControlDiv(cursor, dbid, readingprogress, availprogress, rating, srcTableId)
	renderLndbInfo(itemname)
	renderMangaupdatesInfo(itemname)
	renderItemSearch(itemname)
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
	renderItemSearch(title)
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