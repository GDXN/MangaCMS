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
	if fSize < 1.0e7:
		fStr = fSize/1.0e3
		fStr = "%d K" % int(fStr)
	else:
		fStr = fSize/1.0e6
		fStr = "%0.2f M" % fStr
	return fStr


def buildWhereQuery(tableKey=None, tagsFilter=None, seriesFilter=None):

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
			queryAdditionalArgs.append("%{s}%".format(s=series))

	if seriesFilterArr:
		whereItems.append(" AND ".join(seriesFilterArr))

	if whereItems:
		whereStr = " WHERE %s " % (" AND ".join(whereItems))
	else:
		whereStr = ""

	return whereStr, queryAdditionalArgs

colours = {
	# Download Status
	"failed"          : "000000",
	"no match"        : "FF9999",
	"moved"           : "FFFF99",
	"downloaded"      : "99FF99",
	"processing"      : "9999FF",
	"queued"          : "FF77FF",
	"created-dir"     : "FFE4B2",
	"not checked"     : "FFFFFF",

	# Categories

	"valid cat"  : "FFFFFF",
	"in picked"    : "999999"
	}


%>

<%namespace name="ut" file="utilities.mako"/>


---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

<%def name="genMangaTable(flags='', limit=100, offset=0, distinct=False, tableKey='mt')">
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
	else:
		groupStr = ""


	whereStr, queryAdditionalArgs = buildWhereQuery(tableKey, None, None)
	params = tuple(queryAdditionalArgs)+(limit, offset)

	query = '''SELECT dbId,
						dlState,
						sourceSite,
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
						FROM AllMangaItems
						{query}
						{group}
						ORDER BY retreivalTime DESC
						LIMIT ?
						OFFSET ?;'''.format(query=whereStr, group=groupStr)

	ret = cur.execute(query, params)
	tblCtntArr = ret.fetchall()
	%>
	% for row in tblCtntArr:
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

		cleanedName = nt.sanitizeString(seriesName)
		itemInfo = rating = nt.dirNameProxy[cleanedName]
		if itemInfo["rating"]:
			rating = itemInfo["rating"]
		else:
			rating = ""

		addDate = time.strftime('%y-%m-%d %H:%M', time.localtime(retreivalTime))



		if dlState == 2:
			statusColour = colours["downloaded"]
		elif dlState == 1:
			statusColour = colours["processing"]
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
				locationColour = colours["in picked"]
			elif "newdir" in flags:
				locationColour = colours["created-dir"]
			else:
				locationColour = colours["valid cat"]
		else:
			locationColour = colours["failed"]
			filePath = "N.A."



		%>
		<tr class="${sourceSite}_row">
			<td>${ut.timeAgo(retreivalTime)}</td>
			<td bgcolor=${statusColour} class="showTT" title="${filePath}"></td>
			<td bgcolor=${locationColour} class="showTT" title="${filePath}"></td>
			<td>${ut.createReaderLink(seriesName.title(), itemInfo)}</td>
			<td>${originName}</td>
			<td>${rating}</td>
			<td>${addDate}</td>
		</tr>
	% endfor

	</table>
</%def>


---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

<%def name="genPronTable(siteSource, limit=100, offset=0, tagsFilter=None, seriesFilter=None)">
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

	offset = offset * limit
	whereStr, queryAdditionalArgs = buildWhereQuery(siteSource, tagsFilter, seriesFilter)
	params = tuple(queryAdditionalArgs)+(limit, offset)

	# print("Params = ", params)
	# print("whereStr = ", whereStr)

	cur = sqlCon.cursor()
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
								FROM AllMangaItems
								{query}
								ORDER BY retreivalTime
								DESC LIMIT ?
								OFFSET ?;'''.format(query = whereStr), params)

	tblCtntArr = ret.fetchall()
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

		# % for rowid, addDate, processing, downloaded, dlName, dlLink, itemTags, dlPath, fName in tblCtntArr:

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
			statusColour = colours["downloaded"]
		elif dlState == 1:
			statusColour = colours["processing"]
		else:
			statusColour = colours["queued"]
		if fSize == -2:
			fSizeStr = "No File"
		elif fSize < 0:
			fSizeStr = "Unk Err %s" % fSize

		else:
			fSizeStr = fSizeToStr(fSize)

		if sourceSite == "fu":
			linkPage = "itemsFufufuu"
		elif sourceSite == "djm":
			linkPage = "itemsDjm"
		else:
			linkPage = "LOLNONE"
			print("WAT?", sourceSite)

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
				<td>${originName}</td>
			% else:
				<td><a href="/pron/${linkPage}/${dbId}">${originName}</a></td>
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
			<th class="uncoloured" width="2.5%">MtID</th>
			<th class="uncoloured" width="2.5%">MuID</th>
			<th class="uncoloured" width="40%">MT Name</th>
			<th class="uncoloured" width="40%">BU Name</th>
			<th class="uncoloured" width="5%">Rating</th>
			<th class="uncoloured" width="5%">Edit</th>


		</tr>



	<%

	whereStr, queryAdditionalArgs = buildWhereQuery(tagsFilter, seriesFilter)
	params = tuple(queryAdditionalArgs)


	if sortKey == "update":
		sortKey = "ORDER BY lastChanged DESC"
	elif sortKey == "mtName":
		sortKey = "ORDER BY mtName,buName ASC"
	elif sortKey == "buName":
		sortKey = "ORDER BY buName,mtName ASC"
	elif sortKey == "aggregate":
		sortKey = ""
	else:
		sortKey = "ORDER BY buName,mtName ASC"


	cur = sqlCon.cursor()
	query = '''SELECT 			dbId,
								mtName,
								mtId,
								mtTags,
								mtList,
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
		mtName = inArr[1]
		buName = inArr[5]
		if not buName and not mtName:
			raise ValueError("No keys at all?")
		elif not mtName:
			return buName.lower()
		elif not buName:
			return mtName.lower()

		mtName = mtName.lower()
		buName = buName.lower()

		return mtName if mtName < buName else buName

	if not sortKey:
		# print("Aggregate sort")
		tblCtntArr.sort(key=getSortKey)


	%>

	% for row in tblCtntArr:


		<%
		dbId,            \
		mtName,          \
		mtId,            \
		mtTags,          \
		mtList,          \
		buName,          \
		buId,            \
		buTags,          \
		buList,          \
		readingProgress, \
		availProgress,   \
		rating,          \
		lastChanged = row



		cleanedMtName = None
		cleanedBuName = None

		if mtName != None:
			cleanedMtName = nt.sanitizeString(mtName)
		if buName != None:
			cleanedBuName = nt.sanitizeString(buName)


		if buList in ignoreList:
			continue

		rating = ""

		mtInfo = nt.dirNameProxy[cleanedMtName]
		if mtInfo["item"] != None:
			rating = mtInfo["rating"]

			# print("muInfo", mtInfo)
		else:
			mtInfo = None

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
				<span id="view">${ut.idToLink(mtId=mtId) if mtId else ut.nameToMtSearch(buName, linkText="Search")} </span>
				<span id="edit" style="display:none"> <input type="text" name="mtId" originalValue='${"" if mtId == None else mtId}' value='${"" if mtId == None else mtId}' size=5/> </span>
			</td>
			<td>
				<span id="view">
					% if buId == None and mtName == None:
						wat
					% elif buId == None:
						<form method="post" action="http://www.mangaupdates.com/series.html" id="muSearchForm_${dbId}" target="_blank">
							<input type="hidden" name="act" value="series"/>
							<input type="hidden" name="session" value=""/>
							<input type="hidden" name="stype" value="Title">
							<input type="hidden" name="search" value="${mtName | h}"/>

							<a href="javascript: searchMUForItem('muSearchForm_${dbId}')">Search</a>
						</form>
					% else:
						${ut.idToLink(buId=buId)}
					% endif
				</span>
				<span id="edit" style="display:none"> <input type="text" name="buId" originalValue='${"" if buId == None else buId}' value='${"" if buId == None else buId}' size=5/> </span>
			</td>

			% if mtName != buName:
				<td>
					<span id="view"> ${ut.createReaderLink(mtName, mtInfo)} </span>
					<span id="edit" style="display:none"> <input type="text" name="mtName" originalValue='${"" if mtName == None else mtName}' value='${"" if mtName == None else mtName}' size=35/> </span>
				</td>
				<td>
					<span id="view"> ${ut.createReaderLink(buName, buInfo)} </span>
					<span id="edit" style="display:none"> <input type="text" name="buName" originalValue='${"" if buName == None else buName}' value='${"" if buName == None else buName}' size=35/> </span>
				</td>
			% else:
				<td colspan=2> <center>${ut.createReaderLink(mtName, mtInfo)}</center></td>
			% endif
			<td> ${rating} </td>
			<td>
			% if mtName != buName or not mtId or not buId:
				<a href="#" id='buttonid_${dbId}' onclick="ToggleEdit('${dbId}');return false;">Edit</a>
			% else:
				<s>Edit</s>
			% endif
			</td>

		</tr>
	% endfor

	</table>
</%def>


---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------




<%def name="genLegendTable()">
	<div class="legend">

		<table border="1px">
			<colgroup>
				% for x in range(len(colours)):
					<col style="width: ${100/len(colours)}%" />
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
	</div>

</%def>
