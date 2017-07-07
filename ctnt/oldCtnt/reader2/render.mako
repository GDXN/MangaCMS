## -*- coding: utf-8 -*-

<%startTime = time.time()%>
<%!
import time
styles = ["skId", "mtMonId", "czId", "mbId", "djMoeId", "navId"]

from natsort import natsorted


import nameTools as nt
import unicodedata
import traceback
import settings
import os.path
import urllib
import re
%>
<%
# print("Rendering")
%>


<%namespace name="ut"              file="/utilities.mako"/>
<%namespace name="sideBar"         file="/gensidebar.mako"/>
<%namespace name="tableGen"        file="/gentable.mako"/>
<%namespace name="reader"          file="/reader2/readBase.mako"/>


<%def name="pickDirTable()">

	<%
	reader.readerBrowseHeader()

	keys = list(settings.mangaFolders.keys())
	keys.sort()

	styleTemp = list(styles)
	%>

	<div class="contentdiv subdiv uncoloured">
	<h3>Managa Directories:</h3>
	% for key in keys:
		<% tblStyle = styleTemp.pop() %>

		<div class="${tblStyle}">
			<a href="/reader2/browse/${key}">${settings.mangaFolders[key]["dir"]}</a>
		</div>
	% endfor
	</div>
	<%
	reader.readerBrowseFooter()
	%>
</%def>





<%def name="renderReader(filePath)">
	<%
	reader.showMangaItems(filePath)
	%>
</%def>



<%def name="renderContents(dictKey, navPath)">

	<%
	dirPath = os.path.join(settings.mangaFolders[dictKey]["dir"], *navPath)
	if not os.path.exists(dirPath):
		reader.invalidKeyContent(message="Directory seems to no longer exist!", title='Error!')
		return

	dirContents = os.listdir(dirPath)

	# If there are more then three "chapter 1" files, sort by volume, and then chapter, otherwise,
	# just sort by chapter.
	VOL_THRESHOLD = 3

	# print(dirContents, dirPath)
	tmp = []
	for item in dirContents:
		chap, vol = nt.extractChapterVol(item)

		itemPath = os.path.join(dirPath, item)
		if not os.path.isdir(itemPath):
			sz = os.path.getsize(itemPath)
			szStr = ut.fSizeToStr(sz)
		else:
			szStr = ''


		tmp.append((vol, chap, item, szStr))

	chap1files = len([item for item in tmp if item[1] == 1])

	if not chap1files > VOL_THRESHOLD:
		dirContents = natsorted(tmp, key=lambda dat: (dat[1], dat))
	else:
		dirContents = natsorted(tmp)
	%>
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
				alert("Item deleted!")
				location.reload();
			}
			else
			{
				alert("ERROR!\n"+status.Message)
			}

		};

		function deleteItem(dict, urlPath)
		{

			var go = confirm("Delete item '"+decodeURIComponent(urlPath)+"'")
			if (go)
			{
				var ret = ({});
				ret["delete-item"] = true;
				ret["src-dict"] = dict;
				ret["src-path"] = urlPath;

				$.ajax("/api", {"data": ret, success: ajaxCallback});
				alert("New value - "+newRating);

			}
		}
	</script>
	<table border="1px" class="mangaFileTable">
		<tr>
			<th class="uncoloured" style='width:30'>Vol</th>
			<th class="uncoloured" style='width:30'>Chp</th>
			<th class="uncoloured">${dirPath}</th>
			<th class="uncoloured" style='width:52'>Size</th>
			<th class="uncoloured" style='width:32'>Del</th>
		</tr>

		% for vol, chap, item, size in dirContents:
			<tr>

				<%

				urlPath = list(navPath)
				urlPath.append(item)

				urlPath = [urllib.parse.quote(bytes(item, 'utf-8')) for item in urlPath]
				urlPath = "/".join(urlPath)
				%>
				<td>${str(vol).rstrip('0').rstrip('.') if vol < 990 and vol > 0 else ''}</td>
				<td>${str(chap).rstrip('0').rstrip('.') if chap > 0 else ''}</td>
				<td><a href="/reader2/browse/${dictKey}/${urlPath}">${item}</a></td>
				<td>${size}</td>
				<td><a id="LinkTest" title="Any Title"  href="#" onclick="deleteItem('${dictKey}', '${urlPath}'); return false; ">Del</a></td>
			</tr>
		% endfor
		 <div style="clear:both"></div>
	</table>

</%def>



<%def name="genDirListing(title, dictKey, navPath)">

	<%
	reader.readerBrowseHeader()
	# At this point, we can be confident that `dirPath` is a path that is actually a valid directory, so list it, and
	# display it's contents

	# print("Navpath = ", navPath)

	%>
	<div class="contentdiv subdiv uncoloured">
	<h3>${title}</h3>

		<div class="inlineLeft">

		<%

		renderContents(dictKey, navPath)
		%>
		</div>
		<%
		if navPath:
			buId = reader.generateInfoSidebar(nt.dirNameProxy[navPath[-1]])
		else:
			buId = None

		%>
		<div style="clear:both"></div>

		<%
		reader.renderHTablesForBuId(buId)
		%>
	</div>
	<%
	reader.readerBrowseFooter()
	%>
</%def>



<%def name="displayItemFilesFromKey(itemKey)">

	<%
	# print("itemKey", itemKey)

	itemDict = nt.dirNameProxy[itemKey]

	# print("ItemDict", itemDict)
	if not itemDict["item"]:

		reader.invalidKey(message="No manga items found for key '%s'" % itemKey)
		return

	fullPath = itemDict['fqPath']
	baseName = fullPath.split("/")[-1]



	# itemTemp = nt.dirNameProxy.getRawDirDict(pathKey)
	# keys = list(itemTemp.keys())
	# keys.sort()

	reader.readerBrowseHeader()
	# At this point, we can be confident that `dirPath` is a path that is actually a valid directory, so list it, and
	# display it's contents

	%>
	<div class="contentdiv subdiv uncoloured">
		<h3>${baseName}</h3>

		<div class='watwat'>
			<%

			haveItem = False

			for dirDictKey in nt.dirNameProxy.getDirDicts().keys():
				itemDictTemp = nt.dirNameProxy.getFromSpecificDict(dirDictKey, itemKey)
				if itemDictTemp and itemDictTemp["fqPath"]:
					key, navPath = itemDictTemp["sourceDict"], (itemDictTemp["item"], )
					if navPath:
						haveItem = True
						renderContents(dirDictKey, navPath)
			%>


		</div>
		<div style='float:right'>
			<%
			if haveItem:
				buId = reader.generateInfoSidebar(itemDict)
			else:
				# Probably excessive error checking, since we should be confident we have an item from above.
				reader.invalidKey(message="Could not find anything for that key. Are you sure it's correct?")
				buId = None
			%>
		</div>
		<div>
			${tableGen.genMangaTable(seriesName=itemKey, limit=None, includeUploads=True)}
			${tableGen.genLegendTable()}
		</div>
		${reader.renderHTablesForBuId(buId)}
	</div>
	<%
	reader.readerBrowseFooter()
	%>

</%def>




<%def name="dirContentsContainer(navPath)">

	<%

	if len(navPath) < 1:
		reader.invalidKey(message="No navigation path present? How did this even happen?")
		return

	try:
		dictIndice = int(navPath[0])
	except ValueError:
		reader.invalidKey(message="Specified container path is not a integer!")
		return

	# key "0" puts the system in a special mode, and does lookup in nametools, rather then just specifying a path
	if dictIndice == 0:
		if len(navPath) != 2:
			reader.invalidKey(message="Read mode 0 requires one (and only one) item specified in the path.")
			return
		displayItemFilesFromKey(navPath[1])
		return


	# Ok, we're not in key mode 0, and we have a valid key. Look it up, and render it.
	if not dictIndice in settings.mangaFolders.keys():
		reader.invalidKey(message="Specified container path is not valid!")
		return

	validPaths = [settings.mangaFolders[key]["dir"] for key in settings.mangaFolders.keys()]

	navPath = navPath[1:]
	currentPath = os.path.join(settings.mangaFolders[dictIndice]["dir"], *navPath)


	# Try to block directory traversal shit.
	# It looks like pyramid flattens the URI path before I even get it, but still.
	currentPath = os.path.normpath(currentPath)
	if currentPath.startswith(settings.mangaFolders[dictIndice]["dir"].rstrip('/')):

		if os.path.isfile(currentPath):
			renderReader(currentPath)
		elif os.path.isdir(currentPath):

			prefix = os.path.commonprefix(validPaths)
			title = currentPath[len(prefix):]
			title = "Manga Reader: {dir}".format(dir=title)
			print("Common prefix = ", prefix)


			genDirListing(title, dictIndice, navPath)

		else:

			reader.invalidKey(title="Uh..... That's not a valid file or directory path!")

	else:
		reader.invalidKey(title="No directory traversal bugs for you!",
			message="Directory you attempted to access: {dir}".format(dir=currentPath))
		return

	%>

</%def>



<%
print("Matchdict", request.matchdict)
# If there is no items in the request path, display the root dir
if not len(request.matchdict["page"]):
	pickDirTable()
else:
	dirContentsContainer(request.matchdict["page"])

%>

