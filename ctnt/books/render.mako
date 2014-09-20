## -*- coding: utf-8 -*-


<%namespace name="ut"              file="/utilities.mako"/>
<%namespace name="sideBar"         file="/gensidebar.mako"/>

<%!
import urllib.parse
%>


<%def name="badId()">
	Bad Page Reference!<br>
	Page either not archived, or invalid.

</%def>



<%def name="renderPage(title, contents)">
	<!DOCTYPE html>
	<html>
		<head>
			<title>${title}</title>
			${ut.headerBase()}
		</head>
		<body>
			${sideBar.getSideBar(sqlCon)}
			<div class="bookdiv">

				<div class="subdiv">
					<div class="contentdiv">
						${contents}
					</div>
				</div>
			</div>
		</body>
	</html>

</%def>

<%def name="renderId(itemUrl)">
	<%
	cur = sqlCon.cursor()
	cur.execute("SELECT title, series, mimetype, fsPath, contents FROM book_items WHERE url=%s;", (itemUrl, ))
	page = cur.fetchall()
	if len(page) != 1:
		print("Bad URL", itemUrl)
		badId()
	else:
		title, series, mimetype, fsPath, contents = page.pop()
		renderPage(title, contents)
	%>

</%def>




<%
# print("Rendering")
# print("Matchdict", request.matchdict)
# print("Matchdict", request.params)

if "url" in request.params:
	url = urllib.parse.unquote(request.params["url"])
	renderId(url)
else:
	badId()
%>


