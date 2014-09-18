## -*- coding: utf-8 -*-
<!DOCTYPE html>

<%namespace name="ut"              file="/utilities.mako"/>
<%namespace name="sideBar"         file="/gensidebar.mako"/>

<%!
import bs4
%>


<%def name="badId()">
	Bad PageID!<br>
	Nope!

</%def>



<%def name="renderPage(title, contents)">
	<%
	contents = contents.replace("<html>", "").replace("</html>", "").replace("<body>", "").replace("</body>", "")
	%>
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

<%def name="renderId(pageId)">
	<%
	cur = sqlCon.cursor()
	cur.execute("SELECT title, series, contents FROM tsuki_pages WHERE rowid=%s;", (pageId, ))
	page = cur.fetchall()
	if len(page) != 1:
		badId()
	else:
		title, series, contents = page.pop()
		renderPage(title, contents)
	%>

</%def>




<%
# print("Rendering")
print("Matchdict", request.matchdict)
print("Matchdict", request.params)

if "pageid" in request.params:

	renderId(request.params["pageid"])
else:
	badId()
%>


