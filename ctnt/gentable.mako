## -*- coding: utf-8 -*-
<!DOCTYPE html>
<%!
# Module level!

import re

import time
import datetime
from babel.dates import format_timedelta
import os.path
import urllib.parse

import nameTools as nt

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


def buildWhereQuery(tableKey=None, tagsFilter=None, seriesFilter=None, seriesName=None):

	# print("Building where query. tags=", tagsFilter, "series=", seriesFilter, "tableKey", tableKey)
	if tableKey == None:
		whereItems = []
		queryAdditionalArgs = []

	elif type(tableKey) is str:
		whereItems = ["sourceSite=?"]
		queryAdditionalArgs = [tableKey]

	elif type(tableKey) is list or type(tableKey) is tuple:
		items = []
		queryAdditionalArgs = []
		for key in tableKey:
			items.append("sourceSite=?")
			queryAdditionalArgs.append(key)

		selectStr = " OR ".join(items)    # Convert down to a single string
		selectStr = "(" + selectStr + ")" # and wrap it in parenthesis to make the OR work
		whereItems = [selectStr]
	else:
		raise ValueError("Invalid table-key type")

	tagsFilterArr = []
	if tagsFilter != None:
		for tag in tagsFilter:
			tagsFilterArr.append(" tags LIKE ? ")
			queryAdditionalArgs.append("%{s}%".format(s=tag))

	if tagsFilterArr:
		whereItems.append(" AND ".join(tagsFilterArr))

	seriesFilterArr = []
	if seriesFilter != None:
		for series in seriesFilter:
			seriesFilterArr.append(" seriesName LIKE ? ")
			series = nt.getCanonicalMangaUpdatesName(series)
			queryAdditionalArgs.append("%{s}%".format(s=series))

	seriesNameArr = []
	if seriesName != None:
		seriesFilterArr.append(" seriesName=? ")
		series = nt.getCanonicalMangaUpdatesName(seriesName)
		queryAdditionalArgs.append("{s}".format(s=series))

	if seriesFilterArr:
		whereItems.append(" AND ".join(seriesFilterArr))
	if seriesNameArr:
		whereItems.append(" AND ".join(seriesNameArr))

	if whereItems:
		whereStr = " WHERE %s " % (" AND ".join(whereItems))
	else:
		whereStr = ""

	# print("tableKey, tagsFilter, seriesFilter", tableKey, tagsFilter, seriesFilter, whereItems)
	# print("Query", whereStr, queryAdditionalArgs)
	return whereStr, queryAdditionalArgs

colours = {
	# Download Status
	"failed"          : "000000",
	"no match"        : "FF9999",
	"moved"           : "FFFF99",
	"Done"            : "99FF99",
	"working"         : "9999FF",
	"queued"          : "FF77FF",
	"new dir"         : "FFE4B2",

	# Categories

	"valid cat"  : "FFFFFF",
	"picked"    : "999999"
	}


%>

<%namespace name="ut" file="utilities.mako"/>
<%namespace name="ap" file="activePlugins.mako"/>


---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

<%def name="genMangaTable(flags='', limit=100, offset=0, distinct=False, tableKey=None, seriesName=None)">
	<%
	# print("tableGen!")
	%>
	<table border="1px">
		<tr>
				<th class="uncoloured" width="40">Date</th>
				<th class="uncoloured" width="20">St</th>
				<th class="uncoloured" width="20">Lo</th>
				<th class="uncoloured" width="295">Series</th>
				<th class="uncoloured" width="350">BaseName</th>
				<th class="uncoloured" width="40">Rating</th>
				<th class="uncoloured" width="105">DLTime</th>
		</tr>

	<%
	cur = sqlCon.cursor()

	if flags != '':
		print("Query string not properly generated at the moment")
		print("FIX ME!")


	if distinct:
		groupStr = "GROUP BY seriesName"
		orderBy  = "ORDER BY MAX(retreivalTime) DESC"
	else:
		groupStr = ""
		orderBy  = "ORDER BY retreivalTime DESC"

	# print("building query")

	whereStr, queryAdditionalArgs = buildWhereQuery(tableKey, None, seriesName=seriesName)
	params = tuple(queryAdditionalArgs)+(limit, offset)
	# print("Query = ", whereStr, queryAdditionalArgs)
	# print("built")
	# print("Querying...")
	query = '''

		SELECT
				d.dbId,
				d.dlState,
				d.sourceSite,
				d.sourceUrl,
				d.retreivalTime,
				d.sourceId,
				d.seriesName,
				d.fileName,
				d.originName,
				d.downloadPath,
				d.flags,
				d.tags,
				d.note

		FROM MangaItems AS d
			JOIN
				( SELECT dbId
					FROM MangaItems
					{query}
					{group}
					{order}
					LIMIT ?
					OFFSET ?
				) AS di
				ON  di.dbId = d.dbId
		ORDER BY d.retreivalTime DESC;'''.format(query=whereStr, group=groupStr, order=orderBy)

	# print("Query = ", query)
	# print("params = ", params)

	ret = cur.execute(query, params)
	tblCtntArr = ret.fetchall()
	# print("Done")
	%>
	% for row in tblCtntArr:
		<%

		dbId,          \
		dlState,       \
		sourceSite,    \
		sourceUrl,     \
		retreivalTime, \
		sourceId,      \
		sourceSeriesName,    \
		fileName,      \
		originName,    \
		downloadPath,  \
		flags,         \
		tags,          \
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
		elif dlState == 1:
			statusColour = colours["working"]
		else:
			statusColour = colours["queued"]


		if downloadPath and fileName:
			filePath = os.path.join(downloadPath, fileName)
			if "=0=" in downloadPath:
				if os.path.exists(filePath):
					locationColour = colours["no match"]
				else:
					locationColour = colours["moved"]
			elif "/MP/" in downloadPath and not "picked" in flags:
				locationColour = colours["picked"]
			elif "newdir" in flags:
				locationColour = colours["new dir"]
			else:
				locationColour = colours["valid cat"]
		else:
			if dlState == 0:

				locationColour = colours["queued"]
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
		toolTip += "sourceUrl: " + sourceUrl


		%>
		<tr class="${sourceSite}_row">
			<td>${ut.timeAgo(retreivalTime)}</td>
			<td bgcolor=${statusColour} class="showTT" title="${toolTip}"></td>
			<td bgcolor=${locationColour} class="showTT" title="${toolTip}"></td>
			<td>${ut.createReaderLink(seriesName.title(), itemInfo)}</td>
			<td>${"<strike>" if "deleted" in tags else ""}${originName}${"</strike>" if "deleted" in tags else ""}</td>
			<td>${rating}</td>
			<td>${addDate}</td>
		</tr>
	% endfor

	</table>
</%def>


---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

<%def name="genPronTable(siteSource=None, limit=100, offset=0, tagsFilter=None, seriesFilter=None)">
	<table border="1px">
		<tr>

			<th class="uncoloured" width="5%">Date</th>
			<th class="uncoloured" width="3%">St</th>
			<th class="uncoloured" width="18%">Path</th>
			<th class="uncoloured" width="25%">FileName</th>
			<th class="uncoloured" width="30%">Tags</th>
			<th class="uncoloured" width="8%">Size</th>
			<th class="uncoloured" width="8%">DLTime</th>


		</tr>

	<%
	print("Table rendering begun")
	offset = offset * limit
	whereStr, queryAdditionalArgs = buildWhereQuery(siteSource, tagsFilter, seriesFilter)
	params = tuple(queryAdditionalArgs)+(limit, offset)

	# print("Params = ", params)
	# print("whereStr = ", whereStr)

	cur = sqlCon.cursor()

	print("Query")
	ret = cur.execute('''SELECT 	dbId,
									sourceSite,
									dlState,
									sourceUrl,
									retreivalTime,
									sourceId,
									seriesName,
									fileName,
									originName,
									downloadPath,
									flags,
									tags,
									note
								FROM HentaiItems
								{query}
								ORDER BY retreivalTime
								DESC LIMIT ?
								OFFSET ?;'''.format(query = whereStr), params)

	tblCtntArr = ret.fetchall()
	print("Queried")
	%>

	% for row in tblCtntArr:
		<%

		dbId,          \
		sourceSite,    \
		dlState,       \
		sourceUrl,     \
		retreivalTime, \
		sourceId,      \
		seriesName,    \
		fileName,      \
		originName,    \
		downloadPath,  \
		flags,         \
		tags,          \
		note = row

		dlState = int(dlState)

		# % for rowid, addDate, working, downloaded, dlName, dlLink, itemTags, dlPath, fName in tblCtntArr:

		addDate = time.strftime('%y-%m-%d %H:%M', time.localtime(retreivalTime))

		if not downloadPath and not fileName:
			fSize = -2
			filePath = "NA"

		else:
			try:
				filePath = os.path.join(downloadPath, fileName)
				if os.path.exists(filePath):
					fSize = os.path.getsize(filePath)
				else:
					fSize = -2
			except OSError:
				fSize = -1

		if  dlState == 2 and fSize < 0:
			statusColour = colours["failed"]
		elif dlState == 2:
			statusColour = colours["Done"]
		elif dlState == 1:
			statusColour = colours["working"]
		else:
			statusColour = colours["queued"]
		if fSize == -2:
			fSizeStr = "No File"
		elif fSize < 0:
			fSizeStr = "Unk Err %s" % fSize

		else:
			fSizeStr = fSizeToStr(fSize)


		if not tags:
			tags = ""

		if seriesName and "»" in seriesName:
			seriesNames = seriesName.split("»")
		else:
			seriesNames = [str(seriesName)]



		%>
		<tr class="${sourceSite}_row">

			<td>${ut.timeAgo(retreivalTime)}</td>
			<td bgcolor=${statusColour} class="showTT" title="${dbId}, ${filePath}"></td>
			<td>
			## Messy hack that prevents the "»" from being drawn anywhere but *inbetween* tags in the path
				% for i, seriesName in enumerate(seriesNames):
					${'»'*bool(i)}
					<a href="/itemsPron?bySeries=${seriesName.strip()|u}">${seriesName}</a>
				% endfor
			</td>



			% if fSize <= 0:
				<td>${"<strike>" if "deleted" in tags else ""}${originName}${"</strike>" if "deleted" in tags else ""}</td>
			% else:
				<td><a href="/pron/read/${dbId}">${originName}</a></td>
			% endif


			% if tags != None:
				<td>

				% for tag in tags.split():
					<a href="/itemsPron?byTag=${tag.strip()|u}">${tag}</a>
				% endfor
				</td>
			% else:
				<td>(No Tags)</td>
			% endif

			% if fSize <= 0:
				<td bgcolor=${colours["no match"]}>${fSizeStr}</td>
			% else:
				<td>${fSizeStr}</td>
			% endif

			<td>${addDate}</td>

		</tr>
	% endfor

	</table>
</%def>



---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------



<%def name="genMangaSeriesTable(ignoreList=None, tagsFilter=None, seriesFilter=None, sortKey=None)">
	<table border="1px">
		<tr>

			<th class="uncoloured" width="5%">Last Update</th>
			<th class="uncoloured" width="2.5%">MuID</th>
			<th class="uncoloured" width="40%">Mu Name</th>
			<th class="uncoloured" width="5%">Rating</th>
			<th class="uncoloured" width="5%">Edit</th>


		</tr>



	<%

	whereStr, queryAdditionalArgs = buildWhereQuery(tagsFilter, seriesFilter)
	params = tuple(queryAdditionalArgs)


	if sortKey == "update":
		sortKey = "ORDER BY lastChanged DESC"
	elif sortKey == "buName":
		sortKey = "ORDER BY buName ASC"
	elif sortKey == "aggregate":
		sortKey = ""
	else:
		sortKey = "ORDER BY buName ASC"


	cur = sqlCon.cursor()
	query = '''SELECT 			dbId,
								buName,
								buId,
								buTags,
								buList,
								readingProgress,
								availProgress,
								rating,
								lastChanged
								FROM MangaSeries
								{query}
								{orderBy};'''.format(query=whereStr, orderBy=sortKey)

	# print ("Query = ", query)
	ret = cur.execute(query, params)
	tblCtntArr = ret.fetchall()

	ratingShow = "all"

	if "rated" in request.params:
		if request.params["rated"] == "unrated":
			ratingShow = "unrated"
		elif request.params["rated"] == "rated":
			ratingShow = "rated"

	def getSortKey(inArr):
		buName = inArr[1]
		return buName.lower()


	if not sortKey:
		# print("Aggregate sort")
		tblCtntArr.sort(key=getSortKey)


	%>

	% for row in tblCtntArr:


		<%
		dbId,            \
		buName,          \
		buId,            \
		buTags,          \
		buList,          \
		readingProgress, \
		availProgress,   \
		rating,          \
		lastChanged = row



		cleanedBuName = None

		if buName != None:
			cleanedBuName = nt.sanitizeString(buName)


		if buList in ignoreList:
			continue

		rating = ""


		buInfo = nt.dirNameProxy[cleanedBuName]
		if buInfo["item"] != None:
			rating = buInfo["rating"]

			# print("buInfo", buInfo)
		else:
			buInfo = None

		if ratingShow == "unrated" and rating != "":
			continue
		elif ratingShow == "rated" and rating == "":
			continue


		%>
		<tr id='rowid_${dbId}'>
			<td>${ut.timeAgo(lastChanged)}</td>
			<td>
				<span id="view">
					% if buId == None:
						<form method="post" action="http://www.mangaupdates.com/series.html" id="muSearchForm_${dbId}" target="_blank">
							<input type="hidden" name="act" value="series"/>
							<input type="hidden" name="session" value=""/>
							<input type="hidden" name="stype" value="Title">


							<a href="javascript: searchMUForItem('muSearchForm_${dbId}')">Search</a>
						</form>
					% else:
						${ut.idToLink(buId=buId)}
					% endif
				</span>
				<span id="edit" style="display:none"> <input type="text" name="buId" originalValue='${"" if buId == None else buId}' value='${"" if buId == None else buId}' size=5/> </span>
			</td>

			<td>
				<span id="view"> ${ut.createReaderLink(buName, buInfo)} </span>
				<span id="edit" style="display:none"> <input type="text" name="buName" originalValue='${"" if buName == None else buName}' value='${"" if buName == None else buName}' size=35/> </span>
			</td>
			<td> ${rating} </td>
			<td>
			<a href="#" id='buttonid_${dbId}' onclick="ToggleEdit('${dbId}');return false;">Edit</a>
			</td>

		</tr>
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
							<td style='padding-left: 5px; padding-right: 5px; width: 100px;'>From</td>
						</tr>
						<tr class="${row}">
							<td style='padding-left: 5px; padding-right: 5px; width: 100px;'>${name}</td>
						</tr>
				</table>
			% endfor
		</div>
	</div>

</%def>
