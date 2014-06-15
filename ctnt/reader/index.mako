## -*- coding: utf-8 -*-
<!DOCTYPE html>
<%startTime = time.time()%>


<%namespace name="reader" file="/reader/readBase.mako"/>
<%!
# Module level!
import time
import datetime
from babel.dates import format_timedelta
import os.path
import os
import urllib.parse

from natsort import natsorted

from operator import itemgetter

import nameTools as nt
import unicodedata
import traceback
import settings

styles = ["mtMainId", "mtSubId", "djMoeId", "fuFuId"]


def dequoteDict(inDict):
	ret = {}
	for key in inDict.keys():
		ret[key] = urllib.parse.unquote_plus(inDict[key])
	return ret

def getNotInDBItems(cur):

	monitored = []
	monitorItems = {}
	for item in monitored:
		nameClean = nt.sanitizeString(item[2])

		monitorItems[nameClean] = item

	return monitorItems


%>

<%namespace name="tableGenerators" file="/gentable.mako"/>
<%namespace name="sideBar" file="/gensidebar.mako"/>
<%namespace name="ut"              file="/utilities.mako"/>


<%def name="pickDirTable()">
	<%
	keys = list(settings.mangaFolders.keys())
	keys.sort()

	styleTemp = list(styles)
	%>

	<div class="contentdiv subdiv uncoloured">
	<h3>Managa Directories:</h3>
	% for key in keys:
		<% tblStyle = styleTemp.pop() %>

		<div class="${tblStyle}">
			<a href="/reader/${key}">${settings.mangaFolders[key]["dir"]}</a>
		</div>
	% endfor
	</div>
</%def>

<%def name="displayDirContentsTable(dictKey)">
	<div class="contentdiv subdiv uncoloured">
		<h3>Folder: ${settings.mangaFolders[dictKey]["dir"]}</h3>
		<%
		itemTemp = nt.dirNameProxy.getRawDirDict(dictKey)
		keys = list(itemTemp.keys(), key=lambda y: y.lower())
		keys = natsorted(keys)

		%>
		<table border="1px">
			<tr>
				<th class="uncoloured" width="200">BaseName</th>
				<th class="uncoloured" width="350">Path</th>
			</tr>
			% for key in keys:
				<tr>
					<td><a href="/reader/${dictKey}/${urllib.parse.quote(key)}">${key.title() | h}</a></td>
					<td><a href="/reader/${dictKey}/${urllib.parse.quote(key)}">${itemTemp[key] | h}</a></td>
				</tr>
			% endfor
		</table>
	</div>
</%def>

<%def name="displayItemFiles(dictKey, itemKey)">


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
				$('#rating-status').html("✓");
				location.reload();
			}
			else
			{
				$('#rating-status').html("✗");
				alert("ERROR!\n"+status.Message)
			}

		};
		function ratingChange(newRating)
		{
			$('#rating-status').html("❍");

			var ret = ({});
			ret["change-rating"] = "${itemKey}";
			ret["new-rating"] = newRating;
			$.ajax("/api", {"data": ret, success: ajaxCallback});
			// alert("New value - "+newRating);
		}
	</script>


	<div class="contentdiv subdiv uncoloured">
		<%

		itemDict = nt.dirNameProxy[itemKey]

		fullPath = itemDict['fqPath']
		baseName = fullPath.split("/")[-1]



		# itemTemp = nt.dirNameProxy.getRawDirDict(pathKey)
		# keys = list(itemTemp.keys())
		# keys.sort()

		mtItems = getNotInDBItems(sqlCon.cursor())
		name = nt.sanitizeString(itemDict["item"], flatten=False)
		print(name)
		haveMt, mtLink, haveBu, buLink, buTags, buGenre, buList = ut.getItemInfo(name)

		if haveMt:
			haveMt = "✓"
		else:
			haveMt = "✗"

		if haveBu:
			haveBu = "✓"
		else:
			haveBu = "✗"

		%>
		<h3>Manga: ${baseName}</h3>

		<div class="inlineLeft">
			% for dirDictKey in nt.dirNameProxy.getDirDicts().keys():
				<%

					itemDict = nt.dirNameProxy.getFromSpecificDict(dirDictKey, itemKey)
					if not itemDict["item"]:
						continue
					fullPath = itemDict['fqPath']
					baseName = fullPath.split("/")[-1]

					items = os.listdir(fullPath)
					items.sort()
				%>
				<table border="1px" class="mangaFileTable">
					<tr>
						<th class="uncoloured" width="700">${itemDict["fqPath"]}</th>
					</tr>

					% for item in items:
						<tr>
							<!-- <% print("Item type = ", type(item)) %> -->
							<td><a href="/reader/${dirDictKey}/${urllib.parse.quote(itemKey)}/${urllib.parse.quote(bytes(item, 'utf-8'))}">${item}</a></td>
						</tr>
					% endfor
				</table>
			% endfor
		</div>

		<div class="readerInfo" id="searchDiv">

			<div class="lightRect itemInfoBox">
				 ${baseName}
			</div>

			<div class="lightRect itemInfoBox">
				${haveMt} ${mtLink}
			</div>

			<div class="lightRect itemInfoBox">
				${haveBu} ${buLink}
				<form method="post" action="http://www.mangaupdates.com/series.html" id="muSearchForm" target="_blank">
					<input type="hidden" name="act" value="series"/>
					<input type="hidden" name="session" value=""/>
					<input type="hidden" name="stype" value="Title">
					<input type="hidden" name="search" value="${itemKey | h}"/>

				</form>
			</div>
			<div class="lightRect itemInfoBox">
				Rating<br>
				<%
				rtng = itemDict["rating"]
				%>
				<select name="rating" id="rating" onchange="ratingChange(this.value)">
					<option value="-1" ${"selected='selected''" if rtng == "-"     else ""}>-     </option>
					<option value="0"  ${"selected='selected''" if rtng == ""      else ""}>NR    </option>
					<option value="1"  ${"selected='selected''" if rtng == "+"     else ""}>+     </option>
					<option value="2"  ${"selected='selected''" if rtng == "++"    else ""}>++    </option>
					<option value="3"  ${"selected='selected''" if rtng == "+++"   else ""}>+++   </option>
					<option value="4"  ${"selected='selected''" if rtng == "++++"  else ""}>++++  </option>
					<option value="5"  ${"selected='selected''" if rtng == "+++++" else ""}>+++++ </option>
				</select>
				<span id="rating-status">✓</span>
			</div>


			<div class="lightRect itemInfoBox">
				Bu Tags: ${buTags}
			</div>

			<div class="lightRect itemInfoBox">
				Bu Genre: ${buGenre}
			</div>

			<div class="lightRect itemInfoBox">
				Bu List: ${buList}
			</div>


		</div>



	</div>
</%def>




<html>
	<head>
		<title>WAT WAT IN THE READER</title>
		${ut.headerBase()}

	</head>



	<body>


		<div>
			${sideBar.getSideBar(sqlCon)}
			<div class="maindiv">
				<%

				# request.matchdict = dequoteDict(request.matchdict)


				if 'dict' in request.matchdict and 'seriesName' in request.matchdict:
					item = request.matchdict['seriesName']
					dictKey = int(request.matchdict['dict'])
					# print("Series name! - ", item)
					if (not dictKey in settings.mangaFolders) or (not item in nt.dirNameProxy):
						reader.invalidKeyContent()
					else:
						displayItemFiles(dictKey, item)

				elif 'dict' in request.matchdict:
					try:
						dictKey = int(request.matchdict['dict'])
						if dictKey in settings.mangaFolders:
							displayDirContentsTable(dictKey)
						else:
							reader.invalidKeyContent()
					except ValueError:
						traceback.print_exc()
						reader.invalidKeyContent()
				else:
					pickDirTable()

				%>

			</div>
		<div>

		<%
		stopTime = time.time()
		timeDelta = stopTime - startTime
		%>

		<p>This page rendered in ${timeDelta} seconds.</p>

	</body>
</html>