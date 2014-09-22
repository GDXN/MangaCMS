## -*- coding: utf-8 -*-


<%namespace name="ut"              file="/utilities.mako"/>
<%namespace name="sideBar"         file="/gensidebar.mako"/>

<%!
import urllib.parse
import time
import uuid
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







<%def name="lazyTreeNode(treeKey)">
	<%
	curBase = 'item-%s' % uuid.uuid1(0)

	childNum = 0
	# print(trie)

	%>

	<ul>

		<li><input type="checkbox" id="${curBase}" loaded=0 /><label for="${curBase}">${treeKey}</label>
			<ul>
				<li id="${curBase}"><img src='/js/loading.gif' /></li>
			</ul>
		</li>
	</ul>
	<script>
		function checkboxEvent(e)
		{
			input = $('input#${curBase}');
			if (input.is(':checked') && input.attr("loaded") == 0)
			{
				input.attr("loaded", 1)
				$('li#${curBase}').load("/books/render?tree=${urllib.parse.quote(treeKey)}")
			}

		}

		$('#${curBase}').on('change', checkboxEvent);
	</script>

</%def>



<%def name="lazyTreeRender(treeKey)">
	<%
	curBase = 'item-%s' % uuid.uuid1(0)

	childNum = 0
	# print(trie)
	cur = sqlCon.cursor()


	cur.execute("""SELECT DISTINCT(substring(title for {len})) FROM book_items WHERE lower(title) LIKE %s;""".format(len=len(treeKey)+1), (treeKey.lower()+'%', ))
	ret = cur.fetchall()
	print("Have", ret)

	%>
	% if len(ret) > 1:
		% for item, in ret:
			${lazyTreeNode(item)}
		% endfor
	% else:
		render contents
	% endif


</%def>




<%
# print("Rendering")
# print("Matchdict", request.matchdict)
# print("Matchdict", request.params)

if "url" in request.params:
	url = urllib.parse.unquote(request.params["url"])
	renderId(url)
if "tree" in request.params:
	prefix = urllib.parse.unquote(request.params["tree"])
	lazyTreeRender(prefix)
else:
	badId()
%>




