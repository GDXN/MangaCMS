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


		if not showMissingDir and not dataDict['itemInfo']['fqPath']:
				return

		if not showFoundDir and dataDict['itemInfo']['fqPath']:
				return


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
			<td class="padded">
				${ut.createReaderLink(itemInfo["dirKey"], itemInfo) if itemInfo["item"] else "None"}

				% if 'hentai' in (str(dataDict['tags'])+str(dataDict['genre'])).lower():
					<span style='float:right'>
						${ut.createHentaiSearch("Hentai Search", name)}
					</span>
				% endif

			</td>

			% if haveRating == "Unrated":
				<td bgcolor="${colours["hasUnread"]}"  class="padded showTT" mouseovertext="${makeTooltipTable(name, cleanedName, folderName, itemInfo["fqPath"])}">NR</td>
			% elif haveRating == "No Dir Found":
				<td bgcolor="${colours["notInMT"]}"    class="padded showTT" mouseovertext="${makeTooltipTable(name, cleanedName, folderName, itemInfo["fqPath"])}">NDF</td>
			% else:
				<td class="padded showTT" mouseovertext="${makeTooltipTable(name, cleanedName, folderName, itemInfo["fqPath"])}">${rating}</td>
			%endif


			<td class="padded"><a href="http://www.mangaupdates.com/series.html?id=${dataDict["mangaID"]}">BU</a></td>


			% if dataDict["currentChapter"] == -1 and dataDict["readChapter"] == -1:
				## If both entries are -1, the item is from the complete table, so show it's complete.
				<td bgcolor="${colours["upToDate"]}" class="padded">✓</td>
			% elif dataDict["currentChapter"] == -1 or dataDict["readChapter"] >= dataDict["currentChapter"]:
				<td bgcolor="${colours["upToDate"]}" class="padded">${dataDict["readChapter"]}</td>
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

		for dataDict in tblData:
			genRow(dataDict)

		%>

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
			seriesTable.bulist,
			seriesTable.butags,
			seriesTable.bugenre,
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

	tableTopology = ("mangaID", "currentChapter", "readChapter", "seriesName", "listName", 'tags', 'genre')
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


showMissingDir = True
showFoundDir = True

if 'dirFound' in request.params:
	if request.params["dirFound"] == "True":
		showMissingDir = False

	elif request.params["dirFound"] == "False":
		showFoundDir = False

print(showMissingDir, showFoundDir)
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

						<%

						allReadState  = request.params.copy()
						upToDateRead  = request.params.copy()
						outOfDateRead = request.params.copy()


						allReadState["readStatus"]  = "alldate"
						upToDateRead["readStatus"]  = "upToDate"
						outOfDateRead["readStatus"] = "outOfDate"

						allRatings = request.params.copy()
						hasRating = request.params.copy()
						noRating  = request.params.copy()

						allRatings.pop("hasRating", None)
						hasRating["hasRating"] = "True"
						noRating["hasRating"] = "False"


						singleTable = request.params.copy()
						multiTable  = request.params.copy()

						singleTable["flatTable"] = "True"
						multiTable.pop("flatTable", None)


						sortRating = request.params.copy()
						sortNames  = request.params.copy()

						sortRating["ratingSort"] = "True"
						sortNames.pop("ratingSort", None)


						allDirs    = request.params.copy()
						dirFound   = request.params.copy()
						dirMissing = request.params.copy()


						allDirs.pop("dirFound", None)
						dirFound["dirFound"]   = "True"
						dirMissing["dirFound"] = "False"




						#############################################

						read1 = '➔' if ('readStatus' not in request.params or request.params['readStatus'] == 'alldate') else ''
						read2 = '➔' if ('readStatus' in request.params and request.params['readStatus'] == 'upToDate') else ''
						read3 = '➔' if ('readStatus' in request.params and request.params['readStatus'] == 'outOfDate') else ''

						rate1 = '➔' if ('hasRating' not in request.params) else ''
						rate2 = '➔' if ('hasRating' in request.params and request.params['hasRating'] == 'True') else ''
						rate3 = '➔' if ('hasRating' in request.params and request.params['hasRating'] == 'False') else ''

						list1 = '➔' if ('flatTable' not in request.params) else ''
						list2 = '➔' if ('flatTable' in request.params and request.params['flatTable'] == 'True') else ''

						sort1 = '➔' if ('ratingSort' not in request.params) else ''
						sort2 = '➔' if ('ratingSort' in request.params and request.params['ratingSort'] == 'True') else ''

						dir1 = '➔' if ('dirFound' not in request.params) else ''
						dir2 = '➔' if ('dirFound' in request.params and request.params['dirFound'] == 'True') else ''
						dir3 = '➔' if ('dirFound' in request.params and request.params['dirFound'] == 'False') else ''


						%>


						<div class="" style="white-space:nowrap; display: inline-block; margin-left: 10px;">
							Filter read status:
							<ul style="width: 100px;">

								<li>${read1} <a href="bmUpdates?${urllib.parse.urlencode(allReadState)}">All read status</a></li>
								<li>${read2} <a href="bmUpdates?${urllib.parse.urlencode(upToDateRead)}">Up to date</a></li>
								<li>${read3} <a href="bmUpdates?${urllib.parse.urlencode(outOfDateRead)}">Out of date</a></li>
							</ul>
						</div>
						<div class="" style="white-space:nowrap; display: inline-block; margin-left: 10px; vertical-align:top">
							Filter Rating state:
							<ul style="width: 100px;">
								<li>${rate1} <a href="bmUpdates?${urllib.parse.urlencode(allRatings)}">All rating state</a></li>
								<li>${rate2} <a href="bmUpdates?${urllib.parse.urlencode(hasRating)}">Has rating</a></li>
								<li>${rate3} <a href="bmUpdates?${urllib.parse.urlencode(noRating)}">No Rating</a></li>
							</ul>
						</div>

						<div class="" style="white-space:nowrap; display: inline-block; margin-left: 10px; vertical-align:top">
							Grouping:
							<ul style="width: 100px;">
								<li>${list1} <a href="bmUpdates?${urllib.parse.urlencode(multiTable)}">By list</a></li>
								<li>${list2} <a href="bmUpdates?${urllib.parse.urlencode(singleTable)}">Single Table</a></li>
							</ul>
						</div>

						<div class="" style="white-space:nowrap; display: inline-block; margin-left: 10px; vertical-align:top">
							Sorting:
							<ul style="width: 100px;">
								<li>${sort1} <a href="bmUpdates?${urllib.parse.urlencode(sortNames)}">Alphabetically</a></li>
								<li>${sort2} <a href="bmUpdates?${urllib.parse.urlencode(sortRating)}">By Rating</a></li>
							</ul>
						</div>

						<div class="" style="white-space:nowrap; display: inline-block; margin-left: 10px; vertical-align:top">
							Linked to dir:
							<ul style="width: 100px;">
								<li>${dir1} <a href="bmUpdates?${urllib.parse.urlencode(allDirs)}">All Items</a></li>
								<li>${dir2} <a href="bmUpdates?${urllib.parse.urlencode(dirFound)}">Have local Directory</a></li>
								<li>${dir3} <a href="bmUpdates?${urllib.parse.urlencode(dirMissing)}">Missing local directory</a></li>
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
