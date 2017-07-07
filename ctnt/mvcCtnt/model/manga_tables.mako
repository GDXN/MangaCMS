## -*- coding: utf-8 -*-
<!DOCTYPE html>

<%namespace name="ut" file="utilities.mako"/>
<%namespace name="ap" file="activePlugins.mako"/>

<%!
# Module level!

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

import functools
import operator as opclass

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







################################################################################################################################################################################################################
## -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
################################################################################################################################################################################################################
## is this silly? Yes. Is it readable on the sidebar view? Also yes.
## (Plus, it amuses me)
##
##  ######   #######  ##           ######   ######## ##    ##
## ##    ## ##     ## ##          ##    ##  ##       ###   ##
## ##       ##     ## ##          ##        ##       ####  ##
##  ######  ##     ## ##          ##   #### ######   ## ## ##
##       ## ##  ## ## ##          ##    ##  ##       ##  ####
## ##    ## ##    ##  ##          ##    ##  ##       ##   ###
##  ######   ##### ## ########     ######   ######## ##    ##
##



# The two main content tables
mangaTable = sql.Table("mangaitems")
hentaiTable = sql.Table("hentaiitems")

mangaCols = (
		mangaTable.dbid,
		mangaTable.dlstate,
		mangaTable.sourcesite,
		mangaTable.sourceurl,
		mangaTable.retreivaltime,
		mangaTable.sourceid,
		mangaTable.seriesname,
		mangaTable.filename,
		mangaTable.originname,
		mangaTable.downloadpath,
		mangaTable.flags,
		mangaTable.tags,
		mangaTable.note
	)

hentaiCols = (
		hentaiTable.dbid,
		hentaiTable.dlstate,
		hentaiTable.sourcesite,
		hentaiTable.sourceurl,
		hentaiTable.retreivaltime,
		hentaiTable.sourceid,
		hentaiTable.seriesname,
		hentaiTable.filename,
		hentaiTable.originname,
		hentaiTable.downloadpath,
		hentaiTable.flags,
		hentaiTable.tags,
		hentaiTable.note
	)


# and the series table
seriesTable = sql.Table("mangaseries")


seriesCols = (
		seriesTable.dbId,
		seriesTable.buName,
		seriesTable.buId,
		seriesTable.buTags,
		seriesTable.buList,
		seriesTable.readingProgress,
		seriesTable.availProgress,
		seriesTable.rating,
		seriesTable.lastChanged
	)





def buildQuery(srcTbl, cols, **kwargs):

	orOperators = []
	andOperators = []
	if "tableKey" in kwargs and kwargs['tableKey']:
		if type(kwargs['tableKey']) is str:
			orOperators.append((srcTbl.sourcesite == kwargs['tableKey']))
		elif type(kwargs['tableKey']) is list or type(kwargs['tableKey']) is tuple:
			for key in kwargs['tableKey']:
				orOperators.append((srcTbl.sourcesite == key))
		else:
			raise ValueError("Invalid table-key type! Type: '%s'" % type(kwargs['tableKey']))


	if "tagsFilter" in kwargs and kwargs['tagsFilter']:
		for tag in kwargs['tagsFilter']:

			match = '%{key}%'.format(key=tag.lower())
			andOperators.append(sqlo.Like(srcTbl.tags, match))

	if "seriesFilter" in kwargs and kwargs['seriesFilter']:
		for key in kwargs['seriesFilter']:
			match = '%{key}%'.format(key=key.lower())
			andOperators.append(sqlo.Like(srcTbl.seriesname, match))

	if "seriesName" in kwargs and kwargs['seriesName']:

		andOperators.append((srcTbl.seriesname == kwargs['seriesName']))

	# Trigram similarity search uses the '%' symbol. It's only exposed by the python-sql library as the
	# "mod" operator, but the syntax is compatible.
	if 'originTrigram' in kwargs and kwargs['originTrigram']:
		andOperators.append(sqlo.Mod(srcTbl.originname, kwargs['originTrigram']))


	if orOperators:
		orCond = functools.reduce(opclass.or_, orOperators)
		andOperators.append(orCond)
	if andOperators:
		where = functools.reduce(opclass.and_, andOperators)
	else:
		where=None

	query = srcTbl.select(*cols, order_by = sql.Desc(srcTbl.retreivaltime), where=where)


	if "offset" in kwargs and kwargs['offset']:
		query.offset = int(kwargs['offset'])

	if "limit" in kwargs and kwargs['limit']:
		query.limit = int(kwargs['limit'])

	q, p = tuple(query)
	# print("Query = '%s'" % (q, ))
	# print("Params = '%s'" % (p, ))

	return query


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
	"picked"    : "999999",

	# Download Status
	"hasUnread"       : "FF9999",
	"upToDate"        : "99FF99",
	"notInMT"         : "9999FF",


	"created-dir"     : "FFE4B2",
	"not checked"     : "FFFFFF",

	# Categories

	"valid category"  : "FFFFFF",
	"bad category"    : "999999"
	}

%>


################################################################################################################################################################################################################
## -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
################################################################################################################################################################################################################
##
## ##     ##    ###    ##    ##  ######      ###
## ###   ###   ## ##   ###   ## ##    ##    ## ##
## #### ####  ##   ##  ####  ## ##         ##   ##
## ## ### ## ##     ## ## ## ## ##   #### ##     ##
## ##     ## ######### ##  #### ##    ##  #########
## ##     ## ##     ## ##   ### ##    ##  ##     ##
## ##     ## ##     ## ##    ##  ######   ##     ##
##

<%def name="lazyFetchMangaItems(**kwargs)">
	<%

		# flags          = '',
		# limit          = 100,
		# offset         = 0,
		# distinct       = False,
		# tableKey       = None,
		# seriesName     = None,
		# getErrored     = False,
		# includeUploads = False

		start = time.time()

		if kwargs['distinct'] and kwargs['seriesName']:
			raise ValueError("Cannot filter for distinct on a single series!")

		if kwargs['flags']:
			raise ValueError("TODO: Implement flag filtering!")

		if kwargs['seriesName']:
			# Canonize seriesName if it's not none
			kwargs['seriesName'] = nt.getCanonicalMangaUpdatesName(kwargs['seriesName'])

		query = buildQuery(mangaTable, mangaCols, tableKey=kwargs['tableKey'], seriesName=kwargs['seriesName'])

		if kwargs['getErrored']:
			if query.where:
				query.where &= mangaTable.dlstate < 1
			else:
				query.where  = mangaTable.dlstate < 1

		elif not kwargs['includeUploads']:
			if query.where:
				query.where &= mangaTable.dlstate < 3
			else:
				query.where  = mangaTable.dlstate < 3



		anonCur = sqlCon.cursor()
		anonCur.execute("BEGIN;")

		cur = sqlCon.cursor(name='test-cursor-1')
		cur.arraysize = 250


		query, params = tuple(query)
		cur.execute(query, params)

		if not kwargs['limit']:
			retRows = cur.fetchall()
		else:
			seenItems = []
			rowsBuf = cur.fetchmany()

			rowsRead = 0

			while len(seenItems) < kwargs['offset']:
				if not rowsBuf:
					rowsBuf = cur.fetchmany()
				if not rowsBuf:
					break
				row = rowsBuf.pop(0)
				rowsRead += 1
				if row[6] not in seenItems or not kwargs['distinct']:
					seenItems.append(row[6])

			retRows = []

			while len(seenItems) < kwargs['offset']+kwargs['limit']:
				if not rowsBuf:
					rowsBuf = cur.fetchmany()
				if not rowsBuf:
					break
				row = rowsBuf.pop(0)

				rowsRead += 1
				if (row[6] not in seenItems and "deleted" not in str(row[11])) or not kwargs['distinct']:
					retRows.append(row)
					seenItems.append(row[6])

		cur.close()
		anonCur.execute("COMMIT;")

		return retRows
	%>

</%def>


<%def name="renderMangaRow(row, kwargs)">

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
		ratingNum = nt.ratingStrToFloat(rating)
	else:
		rating = ""
		ratingNum = nt.ratingStrToFloat(rating)

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

	shouldBold = False
	if originName and kwargs['boldNew']:
		chap = nt.extractChapterVol(originName)[0]
		if isinstance(chap, float):
			if chap < 10:
				shouldBold = True


	%>
	<tr class="${sourceSite}_row">
		<td>${ut.timeAgo(retreivalTime)}</td>
		<td bgcolor=${statusColour} class="showTT" mouseovertext="${toolTip}" ${'onclick="event_%s()"' % cellId if cellId else ''}>
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
		<td bgcolor=${locationColour} class="showTT" mouseovertext="${toolTip}"></td>
		<td>${ut.createReaderLink(seriesName.title(), itemInfo)}</td>
		<td>

			% if "phash-duplicate" in tags:
				<span style="text-decoration: line-through; color: red;">
					<span style="color: #000;">
			% elif "deleted" in tags:
				<strike>
			% endif

			% if shouldBold:
				<b>
			% endif

			% if ratingNum >= 2:
				<span style="color: red;">
			% endif

			${originName}


			% if ratingNum >= 2:
				</span>
			% endif

			% if shouldBold:
				</b>
			% endif

			% if "phash-duplicate" in tags:
					</span>
				</span>
			% elif "deleted" in tags:
				</strike>
			% endif

		</td>
		<td>${rating}</td>
		<td>${addDate}</td>
	</tr>


</%def>



<%def name="genMangaTable(*args, **kwargs)">


	<%

	kwargs.setdefault("flags",          '')        # Filter by flag
	kwargs.setdefault("limit",          100)       # Number of rows in generated table
	kwargs.setdefault("offset",         0)         # Shitty pagination system (TODO: Proper persistent cursors!)
	kwargs.setdefault("distinct",       False)     # Limit results to one item per distinct series.
	kwargs.setdefault("tableKey",       None)      # Limit results to source of key `tableKey`
	kwargs.setdefault("seriesName",     None)      # Limit items to series of name `seriesName`. Filtered through MU canonizer.
	kwargs.setdefault("getErrored",     False)     # Only return rows that failed to download
	kwargs.setdefault("includeUploads", False)     # Include uploaded files in table as well.
	kwargs.setdefault("boldNew",        False)     # Bold any items where the found chapter number is < 10



	with sqlCon.cursor() as cur:

		try:
			# ret = cur.execute(query, params)

			tblCtntArr = lazyFetchMangaItems(**kwargs)

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
			${renderMangaRow(row, kwargs)}
		% endfor

	</table>
</%def>





################################################################################################################################################################################################################
## -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
################################################################################################################################################################################################################
##
## ##     ## ######## ##    ## ########    ###    ####
## ##     ## ##       ###   ##    ##      ## ##    ##
## ##     ## ##       ####  ##    ##     ##   ##   ##
## ######### ######   ## ## ##    ##    ##     ##  ##
## ##     ## ##       ##  ####    ##    #########  ##
## ##     ## ##       ##   ###    ##    ##     ##  ##
## ##     ## ######## ##    ##    ##    ##     ## ####



<%def name="renderHentaiRow(row)">
	<%

	dbId,          \
	dlState,       \
	sourceSite,    \
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
	elif dlState == 0:
		statusColour = colours["queued"]
	else:
		statusColour = colours["failed"]

	if fSize == -2:
		fSizeStr = "No File"
	elif fSize < 0:
		fSizeStr = "Unk Err %s" % fSize

	else:
		fSizeStr = ut.fSizeToStr(fSize)


	if not tags:
		tags = ""

	if seriesName and "»" in seriesName:
		seriesNames = seriesName.split("»")
	else:
		seriesNames = [str(seriesName)]



	%>
	<tr class="${sourceSite}_row">

		<td>${ut.timeAgo(retreivalTime)}</td>
		<td bgcolor=${statusColour} class="showHT" mouseovertext="${sourceSite}, ${dbId}, ${filePath}"></td>
		<td>
		## Messy hack that prevents the "»" from being drawn anywhere but *inbetween* tags in the path
			% for i, seriesName in enumerate(seriesNames):
				${'»'*bool(i)}
				<a href="/itemsPron?bySeries=${seriesName.strip()|u}">${seriesName}</a>
			% endfor
		</td>


		<td>
			% if "phash-duplicate" in tags:
				<span style="text-decoration: line-through; color: red;">
					<span style="color: #000;">
			% elif "deleted" in tags:
				<strike>
			% endif

			% if fSize <= 0:
				${originName}
			% else:
				<a href="/pron/read/${dbId}">${originName}</a>
			% endif

			% if "phash-duplicate" in tags:
					</span>
				</span>
			% elif "deleted" in tags:
				</strike>
			% endif
		</td>



		% if tags != None:
			<td>

			% for tag in tags.split():
				<%
				tagname = tag.lower().replace("artist-", "") \
							.replace("authors-", "") \
							.replace("author-", "") \
							.replace("scanlators-", "") \
							.replace("parody-", "") \
							.replace("group-", "") \
							.replace("character-", "") \
							.replace("convention-", "") \
							.strip()
				highlight = False
				doNotWant = False
				if not request.remote_addr in settings.noHighlightAddresses:
					for toHighlighTag in settings.tagHighlight:
						if toHighlighTag in tagname:
							highlight = True
					for noWant in settings.tagNegativeHighlight:
						if noWant in tagname:
							highlight = True
							doNotWant = True

				lStyle = ''
				if doNotWant:
					lStyle = 'style="color:#f00;"'
				elif highlight:
					lStyle = 'style="color:#0B0;"'


				%>
				${"<b>" if highlight else ""}
				${"<strike>" if doNotWant else ""}
				<a ${ lStyle} href="/itemsPron?byTag=${tagname|u}">${tag}</a>
				${"</strike>" if doNotWant else ""}
				${"</b>" if highlight else ""}
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

</%def>


<%def name="genPronTable(siteSource=None, limit=100, offset=0, tagsFilter=None, seriesFilter=None, getErrored=False, originTrigram=None)">

	<%

	offset = offset * limit

	query = buildQuery(hentaiTable,
		hentaiCols,
		tableKey      = siteSource,
		tagsFilter    = tagsFilter,
		seriesFilter  = seriesFilter,
		limit         = limit,
		offset        = offset,
		originTrigram = originTrigram)



	if getErrored:
		if query.where:
			query.where &= hentaiTable.dlstate <= 0
		else:
			query.where  = hentaiTable.dlstate <= 0


	with sqlCon.cursor() as cur:

		query, params = tuple(query)
		if " % " in query:
			query = query.replace(" % ", " %% ")
		cur.execute(query, params)
		tblCtntArr = cur.fetchall()


	%>
	% if tblCtntArr:
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

			% for row in tblCtntArr:
				${renderHentaiRow(row)}
			% endfor

		</table>
	% else:
		<div class="errorPattern">No items!</div>
	% endif
</%def>



################################################################################################################################################################################################################
## -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
################################################################################################################################################################################################################
##
## ##     ##    ###    ##    ##  ######      ###        ######  ######## ########  #### ########  ######
## ###   ###   ## ##   ###   ## ##    ##    ## ##      ##    ## ##       ##     ##  ##  ##       ##    ##
## #### ####  ##   ##  ####  ## ##         ##   ##     ##       ##       ##     ##  ##  ##       ##
## ## ### ## ##     ## ## ## ## ##   #### ##     ##     ######  ######   ########   ##  ######    ######
## ##     ## ######### ##  #### ##    ##  #########          ## ##       ##   ##    ##  ##             ##
## ##     ## ##     ## ##   ### ##    ##  ##     ##    ##    ## ##       ##    ##   ##  ##       ##    ##
## ##     ## ##     ## ##    ##  ######   ##     ##     ######  ######## ##     ## #### ########  ######
##
## This is mostly indended to provide a central point for
## row-generation in the views that involve mangaupdates-
## referenced data
##
##



<%def name="makeTooltipTable(name, cleanedName, folderName, itemPath)">
	<ul>
		<li>Name: '${name | h}'</li>
		<li>Cleaned Name: '${cleanedName | h}'</li>
		<li>DirSort Name: '${folderName | h}'</li>
		% if itemPath:
			<li>Dir: '${itemPath | h}'</li>
		% endif
	</ul>

</%def>


<%def name="genRow(dataDict)">


	<%


		name = dataDict["seriesName"]
		cleanedName = dataDict["seriesName"]

		itemInfo = dataDict["itemInfo"]
		folderName = itemInfo["dirKey"]

		if itemInfo["item"]:
			if not itemInfo["rating"]:
				haveRating = "Unrated"
			if itemInfo["rating"]:
				haveRating = "Rated"

			rating = itemInfo["rating"]


		else:
			rating = None
			haveRating = "No Dir Found"


		%>
		<tr>
			<td class="padded">${name}</td>
			<td class="padded">
				${ut.createReaderLink(itemInfo["dirKey"], itemInfo) if itemInfo["item"] else ""}

				% if 'hentai' in (str(dataDict['tags'])+str(dataDict['genre'])).lower():
					<span style='float:right'>
						${ut.createHentaiSearch("Hentai Search", name)}
					</span>
				% endif

			</td>

			% if haveRating == "Unrated":
				<td bgcolor="${colours["hasUnread"]}"  class="padded showTT" mouseovertext="${makeTooltipTable(name, cleanedName, folderName, itemInfo["fqPath"])}">NR</td>
			% elif haveRating == "No Dir Found":
				<td></td>
			% else:
				<td class="padded showTT" mouseovertext="${makeTooltipTable(name, cleanedName, folderName, itemInfo["fqPath"])}">${rating}</td>
			%endif


			<td class="padded"><a href="http://www.mangaupdates.com/series.html?id=${dataDict["muId"]}">${dataDict["muId"]}</a></td>


			## No translated files at all
			% if dataDict["currentChapter"] == None and dataDict["readChapter"] == None:
				<td class="padded"></td>

			## Translated files, but not on any list.
			% elif dataDict["currentChapter"] != None and dataDict["readChapter"] == None:
				<td class="padded">${dataDict["currentChapter"]}</td>

			## Read chapters, but nothing indicated as translated. Treat it as up-to-date
			% elif dataDict["currentChapter"] == None and dataDict["readChapter"] != None:
				<td bgcolor="${colours["upToDate"]}" class="padded">${dataDict["readChapter"]}</td>

			## If both entries are -1, the item is from the complete table, so show it's complete.
			% elif dataDict["currentChapter"] == -1 and dataDict["readChapter"] == -1:
				<td bgcolor="${colours["upToDate"]}" class="padded">✓</td>

			## At this point, both items are valid integers, and at least one of them isn't -1
			## Therefore, if the read chapter is > -1, and also greater or equal to the current chapter, we're up-to-date
			% elif dataDict["currentChapter"] == -1 or dataDict["readChapter"] >= dataDict["currentChapter"]:
				<td bgcolor="${colours["upToDate"]}" class="padded">${dataDict["readChapter"]}</td>

			## Otherwise, the chapter is out-of-date, so show that.
			% else:
				<td bgcolor="${colours["hasUnread"]}" class="padded">${dataDict["currentChapter"]}</td>
			% endif


			% if dataDict["readChapter"] == -1:
				<td bgcolor="${colours["upToDate"]}" class="padded">Finished</td>
			% elif dataDict["readChapter"] == None:
				<td class="padded"></td>
			% else:
				<td class="padded">${dataDict["readChapter"]}</td>
			% endif
		</tr>

</%def>



<%def name="genSeriesListingTable(tblData)">
	<table border="1px">
		<tr>
				<th class="padded" width="300">Full Name</th>
				<th class="padded" width="300">Cleaned Name</th>
				<th class="padded" width="30">Rating</th>
				<th class="padded" width="30">MuId</th>
				<th class="padded" width="50">Latest Chapter</th>
				<th class="padded" width="60">Read-To Chapter</th>
					</tr>

		<%

		for dataDict in tblData:
			genRow(dataDict)

		%>

	</table>
</%def>

<%def name="genMatchingKeyTable(rows)">


	<%



	%>
	<table border="1px" style="width: 100%;">
		<tr>
				<th class="uncoloured" >Tag</th>
				<th class="uncoloured" style="width: 70px; min-width: 70px;">BuId</th>
				<th class="uncoloured" style="width: 70px; min-width: 70px;">Rating</th>
				<th class="uncoloured" style="width: 70px; min-width: 70px;">Available</th>
				<th class="uncoloured" style="width: 70px; min-width: 70px;">Read</th>
		</tr>

		% for  buName, buId, readingProgress, availProgress, tags, genre  in rows:
			<%
			if not availProgress:
				availProgress = ''
			if not readingProgress:
				readingProgress = ''

			itemInfo = nt.dirNameProxy[buName]


			statusColor = ''
			if readingProgress == -1 and availProgress == -1:
				availProgress = '✓'
				statusColor = 'bgcolor="%s"' % colours["upToDate"]
			elif readingProgress == -1:
				pass
			elif availProgress == -1:
				statusColor = 'bgcolor="%s"' % colours["upToDate"]
			elif readingProgress and availProgress and int(readingProgress) < int(availProgress):
				statusColor = 'bgcolor="%s"' % colours["hasUnread"]
			elif readingProgress:
				statusColor = 'bgcolor="%s"' % colours["upToDate"]

			if readingProgress == -1:
				readingProgress = ''

			if availProgress == -1:
				availProgress = readingProgress

			if not tags:
				tags = ''
			if not genre:
				genre = ''

			%>

			<tr>
				<td class="padded">
					${ut.createReaderLink(buName, itemInfo)}

					% if 'hentai' in (tags+genre).lower():

						<span style='float:right'>
							${ut.createHentaiSearch("Hentai Search", buName)}
						</span>
					% endif
				</td>
				<td class="padded">
					${ut.idToLink(buId)}
				</td>
				<td class="padded">
					${"" if itemInfo['rating'] == None else itemInfo['rating']}
				</td>




				<td  class="padded" ${statusColor}>${availProgress}</td>

				<td class="padded">${readingProgress}</td>

			</tr>
		% endfor


	</table>
</%def>


################################################################################################################################################################################################################
## -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
################################################################################################################################################################################################################
##
## ##       ########  ######   ######## ##    ## ########
## ##       ##       ##    ##  ##       ###   ## ##     ##
## ##       ##       ##        ##       ####  ## ##     ##
## ##       ######   ##   #### ######   ## ## ## ##     ##
## ##       ##       ##    ##  ##       ##  #### ##     ##
## ##       ##       ##    ##  ##       ##   ### ##     ##
## ######## ########  ######   ######## ##    ## ########
##

<%def name="genLegendTable(pron=False, hideSource=False)">
	<%

	limitedColours = {
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
		"picked"    : "999999",

		}

	%>
	<div class="legend">

		<table border="1px" style="width: 100%;">
			<colgroup>
				% for x in range(len(limitedColours)):
					<col style="width: ${int(100/len(limitedColours))}%" />
				% endfor
			</colgroup>
			<tr>
				% for key, value in limitedColours.items():
					<td class="uncoloured legend">${key.title()}</td>
				% endfor
			</tr>
			<tr>
				% for key, value in limitedColours.items():
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
							<td style='padding-left: 5px; padding-right: 5px; width: 70px; font-size: 12px;'>From</td>
						</tr>
						<tr class="${row}">
							<td style='padding-left: 5px; padding-right: 5px; width: 70px; font-size: 12px;'>${name}</td>
						</tr>
				</table>
			% endfor
		</div>
	</div>

</%def>
