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
	dirContents = os.listdir(dirPath)

	chpRe = re.compile(r"(?: chapter |ch|c| )(\d+)")
	volRe = re.compile(r"(?: volume |vol|v)(\d+)")
	# print("Nav path = ", navPath, "dict", dictKey)

	# print("Folder items")
	# for item in dirContents:
	# 	print("File -> '%s'" % item)

	tmp = []
	for item in dirContents:
		chapKey = chpRe.findall(item)
		volKey = volRe.findall(item)

		chapKey = float(chapKey.pop(0)) if chapKey                else 0
		volKey  = float(volKey.pop(0))  if volKey and not chapKey else 0

		tmp.append((volKey, chapKey, item))

	# print("Preprocessed items")
	# for item in tmp:
	# 	print("Item -> '%s'" % (item, ))


	dirContents = natsorted(tmp)


	# print("Sorted items")
	# for item in dirContents:
	# 	print("Item -> '%s'" % (item, ))


	dirContents = [item[2] for item in dirContents]



	# print("Sorted fileNames")
	# for item in dirContents:
	# 	print("Item -> '%s'" % (item, ))

	%>

	<table border="1px" class="mangaFileTable">
		<tr>
			<th class="uncoloured">${dirPath}</th>
		</tr>

		% for item in dirContents:
			<tr>

				<%

				urlPath = list(navPath)
				urlPath.append(item)

				urlPath = [urllib.parse.quote(bytes(item, 'utf-8')) for item in urlPath]
				urlPath = "/".join(urlPath)
				%>
				<td><a href="/reader2/browse/${dictKey}/${urlPath}">${item}</a></td>
			</tr>
		% endfor
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
			reader.generateInfoSidebar(nt.dirNameProxy[navPath[-1]])

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

		<div>
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
		<div>
			<%
			if haveItem:
				reader.generateInfoSidebar(itemDict)
			else:
				# Probably excessive error checking, since we should be confident we have an item from above.
				reader.invalidKey(message="Could not find anything for that key. Are you sure it's correct?")
			%>
		</div>
		<div>
			${tableGen.genMangaTable(seriesName=itemKey, limit=None)}
			${tableGen.genLegendTable()}
			<script type="text/javascript">
				$(document).ready(function() {
				// Tooltip only Text
				$('.showTT').hover(function(){
					// Hover over code
					var title = $(this).attr('title');
					$(this).data('tipText', title).removeAttr('title');
					$('<p class="tooltip"></p>')
					.html(title)
					.appendTo('body')
					.fadeIn('slow');
				}, function() {
					// Hover out code
					$(this).attr('title', $(this).data('tipText'));
					$('.tooltip').remove();
				}).mousemove(function(e) {
					var mousex = e.pageX + 20; //Get X coordinates
					var mousey = e.pageY + 10; //Get Y coordinates
					$('.tooltip')
					.css({ top: mousey, left: mousex })
				});
				});
			</script>
		</div>
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

