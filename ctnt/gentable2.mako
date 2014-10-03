## -*- coding: utf-8 -*-
<!DOCTYPE html>


<%namespace name="ut" file="utilities.mako"/>
<%namespace name="ap" file="activePlugins.mako"/>

<%!
# Module level!
import traceback
import re
import psycopg2
import psycopg2.extras
import time
import datetime
from babel.dates import format_timedelta
import os.path
import urllib.parse
import settings
import nameTools as nt
import uuid
import time

import sql
import sql.operators as sqlo

def compactDateStr(dateStr):
	dateStr = dateStr.replace("months", "mo")
	dateStr = dateStr.replace("month", "mo")
	dateStr = dateStr.replace("weeks", "w")
	dateStr = dateStr.replace("week", "w")
	dateStr = dateStr.replace("days", "d")
	dateStr = dateStr.replace("day", "d")
	dateStr = dateStr.replace("hours", "hr")
	dateStr = dateStr.replace("hour", "hr")
	dateStr = dateStr.replace("minutes", "m")
	dateStr = dateStr.replace("seconds", "s")
	dateStr = dateStr.replace("years", "yrs")
	dateStr = dateStr.replace("year", "yr")
	return dateStr

def fSizeToStr(fSize):

	fStr = fSize/1.0e6
	fStr = "%0.2f M" % fStr
	return fStr




colours = {
	# Download Status
	"failed"          : "000000",
	"no match"        : "FF9999",
	"moved"           : "FFFF99",
	"Done"            : "99FF99",
	"Uploaded"        : "90e0FF",
	"working"         : "9999FF",
	"queued"          : "FF77FF",
	"new dir"         : "FFE4B2",
	"error"           : "FF0000",

	# Categories

	"valid cat"  : "FFFFFF",
	"picked"    : "999999"
	}


table = sql.Table("mangaitems")

cols = (
		table.dbid,
		table.dlstate,
		table.sourcesite,
		table.sourceurl,
		table.retreivaltime,
		table.sourceid,
		table.seriesname,
		table.filename,
		table.originname,
		table.downloadpath,
		table.flags,
		table.tags,
		table.note
	)


# You must import utilities.mako for this to work!
# It relies on monkey-patching the sql.From class which is done in utilities.mako
def buildMangaQuery(cols, tableKey=None, tagsFilter=None, seriesFilter=None, seriesName=None):

	query = table.select(*cols, order_by = sql.Desc(table.retreivaltime))

	if tableKey == None:
		pass
	elif type(tableKey) is str:
		query.addOr(table.sourcesite, tableKey)
	elif type(tableKey) is list or type(tableKey) is tuple:
		for key in tableKey:
			query.addOr(table.sourcesite, key)
	else:
		raise ValueError("Invalid table-key type")


	if tagsFilter != None:
		for tag in tagsFilter:
			query.addOrLike(table.tags, key)

	if seriesFilter != None:
		for key in seriesFilter:

			query.addAndLike(table.seriesName, key)

	if seriesName != None:
		addAnd(query, table.seriesname, seriesName)

	return query

%>

<%



print("Wat?")

%>


---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------



<%def name="fetchMangaItems(flags='', limit=100, offset=0, distinct=False, tableKey=None, seriesName=None, getErrored=False)">
	<%
		start = time.time()

		if distinct and seriesName:
			raise ValueError("Cannot filter for distinct on a single series!")

		if flags:
			raise ValueError("TODO: Implement flag filtering!")


		query = buildMangaQuery(cols, tableKey, seriesName=seriesName)

		if getErrored:
			if query.where:
				query.where &= table.dlState <= 0
			else:
				query.where  = table.dlState <= 0



		anonCur = sqlCon.cursor()
		anonCur.execute("BEGIN;")

		cur = sqlCon.cursor(name='test-cursor-1')
		cur.arraysize = 250


		query, params = tuple(query)
		print(query)
		print(params)
		cur.execute(query, params)

		if not limit:
			retRows = cur.fetchall()
		else:
			seenItems = []
			rowsBuf = cur.fetchmany()

			rowsRead = 0

			while len(seenItems) < offset:
				if not rowsBuf:
					rowsBuf = cur.fetchmany()
				if not rowsBuf:
					break
				row = rowsBuf.pop(0)
				rowsRead += 1
				if row[6] not in seenItems or not distinct:
					seenItems.append(row[6])

			retRows = []

			while len(seenItems) < offset+limit:
				if not rowsBuf:
					rowsBuf = cur.fetchmany()
				if not rowsBuf:
					break
				row = rowsBuf.pop(0)
				rowsRead += 1
				if row[6] not in seenItems or not distinct:
					retRows.append(row)
					seenItems.append(row[6])

		cur.close()
		anonCur.execute("COMMIT;")

		return retRows
	%>

</%def>

<%def name="renderRow(row)">

	<%

	dbId,              \
	dlState,           \
	sourceSite,        \
	sourceUrl,         \
	retreivalTime,     \
	sourceId,          \
	sourceSeriesName,  \
	fileName,          \
	originName,        \
	downloadPath,      \
	flags,             \
	tags,              \
	note = row

	dlState = int(dlState)

	if sourceSeriesName == None:
		sourceSeriesName = "NONE"
		seriesName = "NOT YET DETERMINED"
	else:
		seriesName = nt.getCanonicalMangaUpdatesName(sourceSeriesName)

	# cleanedName = nt.prepFilenameForMatching(sourceSeriesName)
	itemInfo = nt.dirNameProxy[sourceSeriesName]
	if itemInfo["rating"]:
		rating = itemInfo["rating"]
	else:
		rating = ""

	# clamp times to now, if we have items that are in the future.
	# Work around for some time-zone fuckups in the MangaBaby Scraper.
	if retreivalTime > time.time():
		retreivalTime = time.time()

	addDate = time.strftime('%y-%m-%d %H:%M', time.localtime(retreivalTime))

	if not flags:
		flags = ""
	if not tags:
		tags = ""

	if dlState == 2:
		statusColour = colours["Done"]
	elif dlState == 3:
		statusColour = colours["Uploaded"]
	elif dlState == 1:
		statusColour = colours["working"]
	elif dlState == 0:
		statusColour = colours["queued"]
	else:
		statusColour = colours["error"]


	if downloadPath and fileName:
		filePath = os.path.join(downloadPath, fileName)
		if "=0=" in downloadPath:
			if os.path.exists(filePath):
				locationColour = colours["no match"]
			else:
				locationColour = colours["moved"]
		elif settings.pickedDir in downloadPath:
			locationColour = colours["picked"]
		elif "newdir" in flags:
			locationColour = colours["new dir"]
		else:
			locationColour = colours["valid cat"]
	else:
		if dlState == 0:
			locationColour = colours["queued"]
		elif dlState == 3:
			locationColour = colours["valid cat"]
		elif dlState == 1:
			locationColour = colours["working"]
		else:
			locationColour = colours["failed"]
		filePath = "N.A."

	toolTip  = filePath.replace('"', "") + "<br>"
	toolTip += "Original series name: " + sourceSeriesName.replace('"', "") + "<br>"
	toolTip += "Proper MangaUpdates name: " + seriesName.replace('"', "") + "<br>"
	toolTip += "cleanedName: " + itemInfo["dirKey"] + "<br>"
	toolTip += "itemInfo: " + str(itemInfo).replace('"', "") + "<br>"
	toolTip += "rowId: " + str(dbId) + "<br>"
	toolTip += "sourceUrl: " + sourceUrl + "<br>"
	toolTip += "dlState: " + str(dlState) + "<br>"
	toolTip += "tags: " + str(tags) + "<br>"
	toolTip += "Source: " + str(sourceSite) + "<br>"
	if os.path.exists(filePath):
		toolTip += "File found."
	else:
		toolTip += "File is missing!"

	cellId = None
	if dlState < 0:
		cellId = uuid.uuid1(0).hex
	%>
	<tr class="${sourceSite}_row">
		<td>${ut.timeAgo(retreivalTime)}</td>
		<td bgcolor=${statusColour} class="showTT" title="${toolTip}" ${'onclick="event_%s()"' % cellId if cellId else ''}>
			%if dlState==3:
				<center>↑</center>
			%elif dlState < 0:
				<script>

					function ajaxCallback(reqData, statusStr, jqXHR)
					{
						console.log("Ajax request succeeded");
						console.log(reqData);
						console.log(statusStr);

						var status = $.parseJSON(reqData);
						console.log(status)
						if (status.Status == "Success")
						{

							alert("Succeeded!\n"+status.Message)
							// TODO Make this change the page locally, change the cell colours and stuff.
						}
						else
						{
							alert("ERROR!\n"+status.Message)
						}

					};


					function ${"event_%s()" % cellId}
					{
						var reset = window.confirm("Reset download state for item ${dbId}");
						if (reset == true)
						{
							var ret = ({});
							ret["reset-download"] = "${dbId}";
							$.ajax("/api", {"data": ret, success: ajaxCallback});
						}



					}
				</script>
			%endif
		</td>
		<td bgcolor=${locationColour} class="showTT" title="${toolTip}"></td>
		<td>${ut.createReaderLink(seriesName.title(), itemInfo)}</td>
		<td>${"<strike>" if "deleted" in tags else ""}${originName}${"</strike>" if "deleted" in tags else ""}</td>
		<td>${rating}</td>
		<td>${addDate}</td>
	</tr>


</%def>



<%def name="genMangaTable(flags        = '',
							limit      = 100,
							offset     = 0,
							distinct   = False,
							tableKey   = None,
							seriesName = None,
							getErrored = False)">


	<%


	with sqlCon.cursor() as cur:

		try:
			# ret = cur.execute(query, params)

			tblCtntArr = fetchMangaItems(flags, limit, offset, distinct, tableKey, seriesName, getErrored)

		# Catches are needed because if you don't issue a `rollback;`
		# future queries will fail until the rollback is issued.
		except psycopg2.InternalError:
			cur.execute("rollback;")
			raise
		except psycopg2.ProgrammingError:
			cur.execute("rollback;")
			raise


	print("Have data. Rendering.")
	%>

	<table border="1px" style="width: 100%;">
		<tr>
				<th class="uncoloured" style="width: 40px; min-width: 40px;">Date</th>
				<th class="uncoloured" style="width: 20px; min-width: 20px;">St</th>
				<th class="uncoloured" style="width: 20px; min-width: 20px;">Lo</th>
				<th class="uncoloured" style="width: 250px; min-width: 200px;">Series</th>
				<th class="uncoloured">BaseName</th>
				<th class="uncoloured" style="width: 45px; min-width: 45px;">Rating</th>
				<th class="uncoloured" style="width: 105px; min-width: 105px;">DLTime</th>
		</tr>

		% for row in tblCtntArr:
			${renderRow(row)}
		% endfor

	</table>
</%def>



---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------




<%def name="genLegendTable(pron=False, hideSource=False)">
	<div class="legend">

		<table border="1px" style="width: 100%;">
			<colgroup>
				% for x in range(len(colours)):
					<col style="width: ${int(100/len(colours))}%" />
				% endfor
			</colgroup>
			<tr>
				% for key, value in colours.items():
					<td class="uncoloured legend">${key.title()}</td>
				% endfor
			</tr>
			<tr>
				% for key, value in colours.items():
					<td bgcolor="${value}"> &nbsp;</td>
				% endfor
			</tr>
		</table>
		<%

		rows = []
		if not hideSource:
			if not pron:
				for item in [item for item in ap.attr.sidebarItemList if item['type'] == "Manga"]:
					rows.append((item["name"], '{}_row'.format(item['dictKey'])))

			else:
				for item in [item for item in ap.attr.sidebarItemList if item['type'] == "Porn"]:
					rows.append((item["name"], '{}_row'.format(item['dictKey'])))
		%>
		<div>
			% for name, row in rows:
				<table border="1px" style="display:inline-block;">
						<tr class="${row}">
							<td style='padding-left: 5px; padding-right: 5px; width: 67px;'>From</td>
						</tr>
						<tr class="${row}">
							<td style='padding-left: 5px; padding-right: 5px; width: 67px;'>${name}</td>
						</tr>
				</table>
			% endfor
		</div>
	</div>

</%def>
