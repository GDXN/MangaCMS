## -*- coding: utf-8 -*-


<%namespace name="ut"              file="/utilities.mako"/>
<%namespace name="sideBar"         file="/gensidebar.mako"/>

<%!
import urllib.parse
import time
import uuid


def compress_trie(key, childIn):
	if len(childIn) == 1:
		kidKey = list(childIn.keys())[0]
		if isinstance(childIn[kidKey], dict):
			key += kidKey
			return compress_trie(key, childIn[kidKey])
		return key, childIn
	else:
		for kidKey in list(childIn.keys()):
			if isinstance(childIn[kidKey], dict):
				retKey, retDict = compress_trie(kidKey, childIn[kidKey])
				childIn[retKey] = retDict
				if kidKey != retKey:
					del childIn[kidKey]
		return key, childIn

def build_trie(iterItem, getKey=lambda x: x):
	base = {}


	scan = []

	print("Building Trie")
	for item in iterItem:
		scan.append((getKey(item).lower(), item))

	for key, item in scan:

		floating_dict = base
		for letter in key:
			floating_dict = floating_dict.setdefault(letter, {})
		floating_dict["_end_"] = item

	print("Flattening")
	compress_trie('', base)
	print("Done")

	return base


%>


<%def name="badId()">
	Bad Page Reference!<br>
	Page either not archived, or invalid.
</%def>

<%def name="needId()">
	Treeview Requests require a valid source site key.
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







<%def name="lazyTreeNode(rootKey, treeKey)">
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
				$('li#${curBase}').load("/books/render?key=${rootKey}&tree=${urllib.parse.quote(treeKey)}")
			}

		}

		$('#${curBase}').on('change', checkboxEvent);
	</script>

</%def>



<%def name="lazyTreeRender(rootKey, treeKey)">
	<%
	curBase = 'item-%s' % uuid.uuid1(0)

	childNum = 0
	# print(trie)
	cur = sqlCon.cursor()


	cur.execute("""SELECT DISTINCT(substring(title for {len})) FROM book_items WHERE lower(title) LIKE %s AND src=%s;""".format(len=len(treeKey)+1), (treeKey.lower()+'%', rootKey))
	ret = cur.fetchall()
	print("Have", ret)

	%>
	% if len(ret) > 1:
		% for item, in ret:
			${lazyTreeNode(rootKey, item)}
		% endfor
	% else:
		LOLWAT?
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

	if not "key" in request.params:
		needId()
		return

	key = request.params['key']
	if not key in ['tsuki', 'japtem']:
		needId()
		return

	prefix = urllib.parse.unquote(request.params["tree"])
	lazyTreeRender(key, prefix)
else:
	badId()
%>




