## -*- coding: utf-8 -*-

<%startTime = time.time()%>
<%!
import time
styles = ["skId", "mtMonId", "czId", "mbId", "djMoeId", "navId"]





import nameTools as nt
import unicodedata
import traceback
import settings
import os.path
import urllib
%>
<%
print("Rendering")
%>


<%namespace name="ut"              file="/utilities.mako"/>
<%namespace name="sideBar"         file="/gensidebar.mako"/>
<%namespace name="reader" file="/reader2/readBase.mako"/>


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
			<a href="/reader2/browse/${key}">${settings.mangaFolders[key]["dir"]}</a>
		</div>
	% endfor
	</div>
</%def>






<%def name="renderReader(dirPath)">

	<div class="contentdiv subdiv uncoloured">
		<h3>That's a file, yo!</h3>
		Render Reader! <br>${dirPath}
	</div>
</%def>



<%def name="renderContents(dictKey, navPath)">

	<%
	dirPath = os.path.join(settings.mangaFolders[dictKey]["dir"], *navPath)
	dirContents = os.listdir(dirPath)
	dirContents.sort()
	%>
	Render Directory! ${dirPath}


	<table border="1px" class="mangaFileTable">
		<tr>
			<th class="uncoloured" width="700">${"WAT"}</th>
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
	# At this point, we can be confident that `dirPath` is a path that is actually a valid directory, so list it, and
	# display it's contents

	%>
	<div class="contentdiv subdiv uncoloured">
	<h3>${title}</h3>
		<%

		renderContents(dictKey, navPath)
		%>

	</div>

</%def>




<%def name="dirContentsContainer(navPath)">

	<%

	if len(navPath) < 1:
		reader.invalidKeyContent(message="No navigation path present? How did this even happen?")
		return

	try:
		dictIndice = int(navPath[0])
	except ValueError:
		reader.invalidKeyContent(message="Specified container path is not a integer!")

	if not dictIndice in settings.mangaFolders.keys():
		reader.invalidKeyContent(message="Specified container path is not valid!")
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
			reader.invalidKeyContent(title="Uh..... That's not a valid file or directory path!")

	else:
		reader.invalidKeyContent(title="No directory traversal bugs for you!",
			message="Directory you attempted to access: {dir}".format(dir=currentPath))
		return

	%>

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

			# If there is no items in the request path, display the root dir
			if len(request.matchdict["page"]) == 0:
				pickDirTable()
			else:
				dirContentsContainer(request.matchdict["page"])

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