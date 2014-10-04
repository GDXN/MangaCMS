## -*- coding: utf-8 -*-
<!DOCTYPE html>

<%startTime = time.time()%>

<%namespace name="sideBar"         file="gensidebar.mako"/>
<%namespace name="ut"              file="utilities.mako"/>

<%!
# Module level!
import time
import datetime
from babel.dates import format_timedelta
import os.path
import urllib.parse
import sql


import nameTools as nt

import unicodedata

import statusManager as sm

colours = {
	# Download Status
	"hasUnread"       : "FF9999",
	"upToDate"        : "99FF99",
	"notInMT"         : "9999FF",


	"failed"          : "000000",
	"moved"           : "FFFF99",
	"queued"          : "FF77FF",
	"created-dir"     : "FFE4B2",
	"not checked"     : "FFFFFF",

	# Categories

	"valid category"  : "FFFFFF",
	"bad category"    : "999999"}



def getNotInDBItems(cur):

	monitorItems = {}
	# cur.execute('SELECT IDs,addDate,seriesName,items,lastUpdated FROM MtMonitoredIDs;')
	# monitored = cur.fetchall()

	# for item in monitored:
	# 	nameClean = nt.sanitizeString(item[2])

	# 	monitorItems[nameClean] = item

	return monitorItems





###############################################################################################################################################################################################################
# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
###############################################################################################################################################################################################################
#
#  ######  ######## ########  #### ########  ######
# ##    ## ##       ##     ##  ##  ##       ##    ##
# ##       ##       ##     ##  ##  ##       ##
#  ######  ######   ########   ##  ######    ######
#       ## ##       ##   ##    ##  ##             ##
# ##    ## ##       ##    ##   ##  ##       ##    ##
#  ######  ######## ##     ## #### ########  ######
#

seriesTable = sql.Table("mangaseries")


# Not used for anything, just a note, really
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





%>



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
				if not showRatingMissing:
					return
			if itemInfo["rating"]:
				haveRating = "Rated"
				if not showRatingFound:
					return



			rating = itemInfo["rating"]


		else:
			if not showRatingMissing:
				return

			rating = None
			haveRating = "No Dir Found"

		if (dataDict["currentChapter"] > 1) and not showOutOfDate:
			return
		if (dataDict["currentChapter"] == -1) and not showUpToDate:
			return

		%>
		<tr>
			<td class="padded">${dataDict["mangaID"]}</td>
			<td class="padded">${name}</td>
			<td class="padded">${ut.createReaderLink(itemInfo["dirKey"], itemInfo) if itemInfo["item"] else "None"}</td>

			% if haveRating == "Unrated":
				<td bgcolor="${colours["hasUnread"]}"  class="padded showTT" mouseovertext="${makeTooltipTable(name, cleanedName, folderName, itemInfo["fqPath"])}">NR</td>
			% elif haveRating == "No Dir Found":
				<td bgcolor="${colours["notInMT"]}"    class="padded showTT" mouseovertext="${makeTooltipTable(name, cleanedName, folderName, itemInfo["fqPath"])}">NDF</td>
			% else:
				<td class="padded showTT" mouseovertext="${makeTooltipTable(name, cleanedName, folderName, itemInfo["fqPath"])}">${rating}</td>
			%endif


			<td class="padded"><a href="http://www.mangaupdates.com/series.html?id=${dataDict["mangaID"]}">BU</a></td>


			% if dataDict["currentChapter"] == -1:
				% if dataDict["readChapter"] == -1:
					<td bgcolor="${colours["upToDate"]}" class="padded">✓</td>
				% else:
					<td bgcolor="${colours["upToDate"]}" class="padded">${dataDict["readChapter"]}</td>
				% endif
			% else:
				<td bgcolor="${colours["hasUnread"]}" class="padded">${dataDict["currentChapter"]}</td>
			% endif

			% if dataDict["readChapter"] == -1:
				<td class="padded">Finished</td>
			% else:
				<td class="padded">${dataDict["readChapter"]}</td>
			% endif
		</tr>

</%def>



<%def name="genBmUpdateTable(tblData)">
	<table border="1px">
		<tr>
				<th class="padded" width="55">Bu ID</th>
				<th class="padded" width="300">Full Name</th>
				<th class="padded" width="300">Cleaned Name</th>
				<th class="padded" width="30">Rating</th>
				<th class="padded" width="30">MU It</th>
				<th class="padded" width="50">Latest Chapter</th>
				<th class="padded" width="60">Read-To Chapter</th>
					</tr>

		<%
		# print("tableGen")

		if "ratingSort" in request.params and request.params["ratingSort"] == "True":
			# Sort list by rating decending, then seriesName ascending
			tblData.sort(key=lambda x: (nt.ratingStrToInt(x['itemInfo']['rating'])*-1, x["seriesName"]))

		else:
			tblData.sort(key=lambda x: (x["seriesName"]))  # Sort list by seriesName asc

		%>
		% for dataDict in tblData:
			${genRow(dataDict)}
		% endfor

	</table>
</%def>




<%


# Get all items which have a non-null seriesId and BuId,
# zip them all into dicts where {colName : value, ...
# return dicts in list.
def getItemsInLists():
	cols = (
			seriesTable.buid,
			seriesTable.availprogress,
			seriesTable.readingprogress,
			seriesTable.buname,
			seriesTable.bulist
		)

	query = seriesTable.select(*cols)
	query.where = (seriesTable.buid != None) & (seriesTable.bulist != None)

	with sqlCon.cursor() as cur:

		mtItems = getNotInDBItems(cur)
		print("Querying")
		cur.execute(*tuple(query))
		buItems = cur.fetchall()
		print("Query complete")

	ret = []

	tableTopology = ("mangaID", "currentChapter", "readChapter", "seriesName", "listName")
	for item in buItems:
		tmp = dict(zip(tableTopology, item))

		tmp["itemInfo"] = nt.dirNameProxy[tmp["seriesName"]]
		if not tmp["itemInfo"]['rating']:
			tmp["itemInfo"]['rating'] = ''

		ret.append(tmp)

	return ret


def getListDicts(flatten=False):

	items = {}


	for item in getItemsInLists():
		seriesName = item["seriesName"]

		listName = item["listName"].replace(chr(160), " ")  # remove non-breaking spaces.

		if flatten:
			if 'All' in items:
				items['All'].append(item)
			else:
				items['All'] = [item]

		else:
			if listName in items:
				items[listName].append(item)
			else:
				items[listName] = [item]



	reSortTop = ["Win", "Fascinating", "Interesting", "Tablet search"]
	reSortTop.reverse()
	reSortBottom = ["Interesting and Untranslated", "Vaguely Interesting", "Novels of interest", "Good H", "Interesting H", "Meh H", "Complete List"]

	keyList = list(sorted(items.keys()))   # Sort, and then move the "Complete" item to the list end so it displays there instead


	# sort items in the `reSortTop` list up to the top of the list, and items in `reSortBottom` down to the bottom
	for item in keyList:
		for val in reSortBottom:
			if val.lower() == item.lower():  # lower-case, and replace the non-breaking space with a normal space
				keyList.remove(item)
				keyList.append(item)
				break

		for val in reSortTop:
			if val.lower() == item.lower():  # lower-case, and replace the non-breaking space with a normal space
				print("Wat", val, item)
				keyList.remove(item)
				keyList.insert(0, item)
				break


	return keyList, items


showOutOfDate = True
showUpToDate = True

showRatingFound  = True
showRatingMissing = True

flatTable = False

if "readStatus" in request.params:
	if request.params["readStatus"] == "upToDate":
		showOutOfDate = False

	elif request.params["readStatus"] == "outOfDate":
		showUpToDate = False

if "hasRating" in request.params:
	if request.params["hasRating"] == "True":
		showRatingMissing = False

	elif request.params["hasRating"] == "False":
		showRatingFound = False

if "flatTable" in request.params and request.params["flatTable"] == "True":
	flatTable = True

print("Generating table")


%>



<html>
	<head>
		<title>WAT WAT IN THE BATT</title>

		${ut.headerBase()}


	</head>

	<body>

		<div>

			${sideBar.getSideBar(sqlCon)}
			<div class="maindiv">

				<div class="subdiv buMonId" style="padding: 5px;">
					<h3>Baka-Manga Updates</h3>
					<div>

						<div class="" style="white-space:nowrap; display: inline-block; margin-left: 10px;">
							Filter read status:
							<ul style="width: 100px;">

								<li> <a href="bmUpdates?readStatus=alldate">All read status</a></li>
								<li> <a href="bmUpdates?readStatus=upToDate">Up to date</a></li>
								<li> <a href="bmUpdates?readStatus=outOfDate">Out of date</a></li>
							</ul>
						</div>
						<div class="" style="white-space:nowrap; display: inline-block; margin-left: 10px; vertical-align:top">
							Filter Rating state:
							<ul style="width: 100px;">
								<li> <a href="bmUpdates">All rating state</a></li>
								<li> <a href="bmUpdates?hasRating=True">Has rating</a></li>
								<li> <a href="bmUpdates?hasRating=False">No Rating</a></li>
							</ul>
						</div>

						<%

						singleTable = request.params.copy()
						multiTable  = request.params.copy()

						singleTable["flatTable"] = "True"
						multiTable.pop("flatTable", None)


						sortRating = request.params.copy()
						sortNames  = request.params.copy()

						sortRating["ratingSort"] = "True"
						sortNames.pop("ratingSort", None)


						%>

						<div class="" style="white-space:nowrap; display: inline-block; margin-left: 10px; vertical-align:top">
							Grouping:
							<ul style="width: 100px;">
								<li> <a href="bmUpdates?${urllib.parse.urlencode(multiTable)}">By list</a></li>
								<li> <a href="bmUpdates?${urllib.parse.urlencode(singleTable)}">Single Table</a></li>
							</ul>
						</div>



						<div class="" style="white-space:nowrap; display: inline-block; margin-left: 10px; vertical-align:top">
							Sorting:
							<ul style="width: 100px;">
								<li> <a href="bmUpdates?${urllib.parse.urlencode(sortNames)}">Alphabetically</a></li>
								<li> <a href="bmUpdates?${urllib.parse.urlencode(sortRating)}">By Rating</a></li>
							</ul>
						</div>

						<hr>

						<%
						keys, items = getListDicts(flatten=flatTable)
						%>

						% for key in keys:
							<div>
								<div style="margin-top: 10px;">
									<div style="display:inline;"><h4 style="display:inline;">List: ${key}</h4></div>
								</div>
								${genBmUpdateTable(items[key])}
							</div>
						% endfor
					</div>

				</div>
			</div>

		</div>
		<%
		stopTime = time.time()
		timeDelta = stopTime - startTime
		%>

		<p>This page rendered in ${timeDelta} seconds.</p>

	</body>
</html>
