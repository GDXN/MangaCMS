## -*- coding: utf-8 -*-
<!DOCTYPE html>
<html>
<head>
	<title>WAT WAT IN THE BATT</title>
	<link rel="stylesheet" href="style.css">
</head>

<%startTime = time.time()%>

<%namespace name="tableGenerators" file="gentable.mako"/>
<%namespace name="sideBar" file="gensidebar.mako"/>

<%!
# Module level!
import time
import datetime
from babel.dates import format_timedelta
import os.path

import flags
from operator import itemgetter

import nameTools as nt

def ratingStrToValue(ratingStr):
	ret = 0.0
	ret += ratingStr.count('+')
	ret += ratingStr.count('~')*0.5
	ret += ratingStr.count('-')*-1
	if "!" in ratingStr:
		ret += ratingStr.count('!')+ 9999
	return ret

def multikeysort(items, columns):
	# Sort [items] by each attribute in [colums], returning a list
	# Can sort into a list of dictionaries
	# multikeysort([list, of, dicts], ["KeyOne", "KeyTwo"])
	from operator import itemgetter
	comparers = [ ((itemgetter(col[1:].strip()), -1) if col.startswith('-') else (itemgetter(col.strip()), 1)) for col in columns]
	def comparer(left, right):
		for fn, mult in comparers:
			result = cmp(fn(left), fn(right))
			if result:
				return mult * result
		else:
			return 0
	return sorted(items, cmp=comparer)


colours = {
	# Download Status
	"failed"          : "000000",
	"no matching dir" : "FF9999",
	"moved"           : "FFFF99",
	"downloaded"      : "99FF99",
	"processing"      : "9999FF",
	"queued"          : "FF77FF",
	"created-dir"     : "FFE4B2",
	"not checked"     : "FFFFFF",

	# Categories

	"valid category"  : "FFFFFF",
	"bad category"    : "999999"}



%>

<%

def updateDBifneeded():

	# If there is a pageArg that tells us to replace a value in the DB, do that
	# e.g. replaces item with a baseName of originalName with the value of newName

	cur = sqlCon.cursor()

	if "originalName" in request.params and "newName" in request.params:
		print("change name?")
		if isinstance(request.params["originalName"], list) and isinstance(request.params["newName"], list):
			oldName = request.params["originalName"][0]
			newName = request.params["newName"][0]
			if oldName.lower() in items:
				print("have item in query")
				print("Old = ", oldName, "New = ", newName)
				cur.execute('SELECT * FROM links WHERE baseName=?;', (oldName, ))
				print("Counting items that will be changed: ")
				for item in cur.fetchall():
					print("Item = ", item)

				print("Updating DB!?")
				cur.execute('UPDATE links SET baseName=? WHERE baseName=?;', (newName, oldName))
				print(cur.fetchall())
				sqlCon.commit()

			else:
				print("Item = ", oldName)


def processTableData(items):
	print("processing the things!")
	cur = sqlCon.cursor()


	cur.execute('SELECT * FROM links WHERE isMp=1 ORDER BY addDate DESC;')
	mtPicked = cur.fetchall()


	# Iterate over database, storing the most recent instance of each value by looking at the addDate.
	# Items are stored by cleanedName to try to maintain uniqueness
	items = {}
	for addDate, processing, downloaded, dlName, dlLink, baseName, dlPath, fName, isMp, newDir in mtPicked:

		cleanedName = nt.sanitizeString(baseName)
		if not cleanedName in items:
			items[cleanedName] = [addDate, baseName, dlPath]
		else:
			if addDate > items[cleanedName][0]:
				items[cleanedName] = [addDate, baseName, dlPath]



	out = []
	for cleanedName, value in items.items():
		addDate, baseName, dlPath = value
		if cleanedName in nt.dirNameProxy:
			ratingStr = nt.dirNameProxy[cleanedName]['rating']
			ratingNum = ratingStrToValue(ratingStr)

			out.append({"addDate": addDate,
						"cleanedName": cleanedName,
						"baseName": baseName,
						"rating": ratingStr,
						"ratingNum": ratingNum,
						"dlPath": dlPath})
		else:
			out.append({"addDate": addDate,
						"cleanedName": cleanedName,
						"baseName": baseName,
						"rating": "",
						"ratingNum": 0,
						"dlPath": dlPath})
			# print(baseName, addDate)


	# for item in out:
	# 	print(item)

	# Do sort of data list by page arguments
	if "sortby" in request.params:
		if request.params["sortby"] == ["AZ"]:
			# print("sorting by newest")
			out = sorted(out, key=itemgetter('baseName'))

		elif request.params["sortby"] == ["ZA"]:
			# print("sorting by oldest")
			out = sorted(out, key=itemgetter('baseName'), reverse=True)
		elif request.params["sortby"] == ["norating"]:
			# print("sorting by highest rating")
			out = multikeysort(out, ['-ratingNum', 'baseName'])
		elif request.params["sortby"] == ["noratingreverse"]:
			# print("sorting by highest rating")
			out = multikeysort(out, ['ratingNum', 'baseName'])
		else:
			print("no sort parameter!")
			out = sorted(out, key=itemgetter('baseName'))
	else:
		print("no sort parameter!")
		out = sorted(out, key=itemgetter('baseName'))
	return out, ratingsDB

def getNotInDBItems(items, ratings):



	cur.execute('SELECT * FROM MtMonitoredIDs;')
	monitored = cur.fetchall()


	monitorItems = {}
	for item in monitored:
		name = item[2]
		nameClean = nt.sanitizeString(name)
		# print(nameClean in items, name, nameClean)
		monitorItems[nameClean] = item

	ret = []
	for key, value in ratings.items():
		if key not in items and key not in monitorItems:

			value["ratingNum"] = ratingStrToValue(value["rating"])
			value["baseName"] = key
			ret.append(value)

	if "sortby" in request.params:
		if request.params["sortby"] == ["AZ"]:
			# print("sorting by newest")
			ret = sorted(ret, key=itemgetter('baseName'))

		elif request.params["sortby"] == ["ZA"]:
			# print("sorting by oldest")
			ret = sorted(ret, key=itemgetter('baseName'), reverse=True)
		elif request.params["sortby"] == ["norating"]:
			# print("sorting by highest rating")
			ret = multikeysort(ret, ['-ratingNum', 'baseName'])
		elif request.params["sortby"] == ["noratingreverse"]:
			# print("sorting by highest rating")
			ret = multikeysort(ret, ['ratingNum', 'baseName'])
		else:
			print("no sort parameter!")
			ret = sorted(ret, key=itemgetter('baseName'))
	else:
		print("no sort parameter!")
		ret = sorted(ret, key=itemgetter('baseName'))

	return ret

%>



<%def name="genPickedTable(tblData)">
	<table border="1px" style="width:1290px;">
		<tr>
				<th class="uncoloured padded" width="80">Updated</th>
				<th class="uncoloured padded" width="300">Series</th>
				<th class="uncoloured padded" width="300">Updated</th>
				<th class="uncoloured padded" width="60">Rating</th>
				<th class="uncoloured padded" width="110">DLTime</th>
		</tr>

		% for dataDict in tblData:
			<%


			delta = datetime.datetime.now() - datetime.datetime.fromtimestamp(dataDict["addDate"])
			timeDelta = format_timedelta(delta, locale='en_US')
			addDate = time.strftime('%y-%m-%d %H:%M', time.localtime(dataDict["addDate"]))

			%>
			<tr>
				<td class="uncoloured padded">${timeDelta}</td>
				<td class="uncoloured padded">
					BaseName = "${dataDict["baseName"]}"<br>
					CleanedN = "${dataDict["cleanedName"]}"
				</td>
				<td class="uncoloured padded">
					<form>
						<input type="hidden" name="originalName", value="${dataDict["baseName"]}">
						<input type="text"   name="newName",      value="${dataDict["baseName"]}" size=40><br>
						% if "sortby" in request.params:
							<input type="hidden" name="sortby", value="${request.params["sortby"][0]}">
						% endif
						<input type="submit" value="Submit">


					</form>
				</td>
				<td class="uncoloured padded">${dataDict["rating"]}, ${dataDict["ratingNum"]}</td>
				<td class="uncoloured padded">${dataDict["addDate"]}</td>
			</tr>
		% endfor

	</table>
</%def>

<%def name="genNotInDBTable(tblData)">
	<table border="1px" style="width:1290px;">
		<tr>
				<th class="uncoloured padded" width="300">BaseN</th>
				<th class="uncoloured padded" width="300">DirName</th>
				<th class="uncoloured padded" width="60">MTIt</th>
				<th class="uncoloured padded" width="60">MUIt</th>
				<th class="uncoloured padded" width="60">Rating</th>
					</tr>

		% for dataDict in tblData:
			<%

			%>
			<tr>
				<td class="uncoloured padded">${dataDict["baseName"]}</td>
				<td class="uncoloured padded">${dataDict["item"]}</td>
				<td class="uncoloured padded"><a href="http://www.mangatraders.com/search/?term=${dataDict["baseName"]}&Submit=Submit&searchSeries=1">MT</a></td>
				<td class="uncoloured padded"><a href="http://www.mangaupdates.com/search.html?search=${dataDict["baseName"]}">BU</a></td>
				<td class="uncoloured padded">${dataDict["rating"]}</td>
			</tr>
		% endfor

	</table>
</%def>



<%

# ------------------------------------------------------------------------
# This is the top of the main
# page generation section.
# Execution begins here
# ------------------------------------------------------------------------

cur = sqlCon.cursor()



cur.execute('SELECT * FROM links WHERE isMp=1 ORDER BY addDate DESC;')
mtPicked = cur.fetchall()

cur.execute('SELECT COUNT(DISTINCT baseName) FROM links WHERE isMp=1;')
mpDistinct = cur.fetchall()[0][0]

cur.execute('SELECT COUNT(DISTINCT seriesName) FROM MtMonitoredIDs;')
monitoredDistinct = cur.fetchall()[0][0]




items = {}

for addDate, processing, downloaded, dlName, dlLink, baseName, dlPath, fName, isMp, newDir in mtPicked:

	cleanedName = nt.sanitizeString(baseName)
	if not cleanedName in items:
		items[cleanedName] = [addDate, baseName, dlPath]

	else:
		if addDate > items[cleanedName][0]:
			items[cleanedName] = [addDate, baseName, dlPath]




# DB update is processed *before* any data for display is loaded, so changes will be reflected in the returned page.
updateDBifneeded();
if "notInDB" in request.params and request.params["notInDB"] == ["true"]:

	notInDB = getNotInDBItems(items, nt.dirNameProxy)

else:
	print("executing picked fixer")
	out, ratings = processTableData(items)





%>

<body>

<div>

	${sideBar.getSideBar(sqlCon)}
	<div class="maindiv" style="width:1300px">

		<div class="subdiv mtMainId">
			<h3>New MT Series</h3>
			<div class="" style="white-space:nowrap; display: inline-block;">
				View DB items and sort by:
				<ul style="width: 100px;">
					<li> <a href="dbFix?sortby=AZ">Name</a></li>
					<li> <a href="dbFix?sortby=ZA">Name, reversed</a></li>
					<li> <a href="dbFix?sortby=norating">Rating</a></li>
					<li> <a href="dbFix?sortby=noratingreverse">Rating, reversed</a></li>
				</ul>
			</div>
			<div class="" style="white-space:nowrap; display: inline-block; margin-left: 80px;">
				Other views:
				<ul style="width: 100px;">
					<li> <a href="dbFix?notInDB=true&sortby=AZ">Not in DB, sort by name</a></li>
					<li> <a href="dbFix?notInDB=true&sortby=ZA">Not in DB, sort by name, reversed</a></li>
					<li> <a href="dbFix?notInDB=true&sortby=norating">Rating</a></li>
					<li> <a href="dbFix?notInDB=true&sortby=noratingreverse">Rating, reversed</a></li>
				</ul>
			</div>
			% if "notInDB" in request.params and request.params["notInDB"] == ["true"]:		# //////////////////////////////////////////
				<div> <!-- class=""  style="white-space:nowrap; display: inline-block; margin-left: 80px;"> -->
					wat:
					<table>
						<tr>
							<td>Unique items in MP directory: </td>		<td>${len(ratings)}</td>
						</tr>
						<tr>
							<td>Unique MP items in Database: </td>			<td>${mpDistinct}</td>
						</tr>
						<tr>
							<td>Unique MtMon items in Database: </td>			<td>${monitoredDistinct}</td>
						</tr>
						<tr>
							<td>Unique items in MP Dir and not DB: </td>	<td>${len(notInDB)}</td>
						</tr>
						<tr>
							<td>Items that need to be sorted: </td>		<td>${len(items)}</td>
						</tr>
					</table>
				</div>
				${genNotInDBTable(notInDB)}
			% else:																# //////////////////////////////////////////
				${genPickedTable(out)}
			% endif																# //////////////////////////////////////////

		</div>

	</div>
<div>


<%
stopTime = time.time()
timeDelta = stopTime - startTime
%>

<p>This page rendered in ${timeDelta} seconds.</p>

</body>
</html>