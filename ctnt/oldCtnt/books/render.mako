## -*- coding: utf-8 -*-


<%namespace name="ut"              file="/utilities.mako"/>
<%namespace name="sideBar"         file="/gensidebar.mako"/>

<%!
import urllib.parse
import time
import uuid
import settings

def compact_trie(inKey, inDict):

	if len(inDict) == 0:
		raise ValueError("Wat? Item in dict with zero length!")
	elif len(inDict) == 1:

		curKey, curDict = inDict.popitem()

		# Don't munge the end key
		if curKey == "_end_":
			return inKey, {curKey : curDict}

		curKey, curDict = compact_trie(curKey, curDict)
		return inKey+curKey, curDict

	else:   # len(inDict) > 1

		ret = {}
		for key, value in inDict.items():
			if key != "_end_":
				key, value = compact_trie(key, value)
			ret[key] = value

		return inKey, ret


def build_trie(iterItem, getKey=lambda x: x):
	base = {}


	# Build a trie data structure that represents the strings passed using nested dicts
	scan = []
	for item in iterItem:
		scan.append((getKey(item).lower(), item))

	for key, item in scan:

		floating_dict = base
		for letter in key:
			floating_dict = floating_dict.setdefault(letter, {})
		floating_dict["_end_"] = item

	# Flatten cases where nested dicts have only one item. convert {"a": {"b" : sommat}} to {"ab" : sommat}
	key, val = compact_trie('', base)
	out = {key : val}

	return out


%>


<%def name="badId()">
	Error: Bad Page Reference!<br>
	Page either not archived, or invalid.
</%def>

<%def name="needId()">
	Treeview Requests require a valid source site key.
</%def>




<%def name="renderDirectory(inDict, name, keyBase, keyNum, isBase=False)">
	<%
	curBase = 'item-%s' % uuid.uuid1(0)

	childNum = 0

	keys = list(inDict.keys())
	keys.sort()
	%>

	<ul>

		% if not isBase:
			<li><input type="checkbox" id="${curBase}" checked="checked" /><label for="${curBase}">${'Baka-Tsuki' if not name else name}</label>
				<ul>
		% endif
				% for key in keys:
					% if "_end_" in key:
						<%
							url, dbId, title = inDict[key]
						%>

						<li>
							<div id='rowid'>${dbId}</div>
							<div id='rowLink'><a href='/books/render?url=${urllib.parse.quote(url)}'>${title}</a></div>
						</li>
					% else:
						<%
							renderDirectory(inDict[key], name+key, curBase, childNum)
							childNum += 1

						%>
					% endif
				% endfor
		% if not isBase:
			</ul>
		% endif
		</li>
	</ul>
</%def>


<%def name="renderWholeBranch(rootKey, keyBase)">
	<%

		cur = sqlCon.cursor()
		cur.execute("SELECT url, dbid, title FROM book_items WHERE src = %s AND mimetype = %s AND lower(title) LIKE lower(%s) ORDER BY title;", (rootKey, 'text/html', keyBase+'%'))
		ret = cur.fetchall()

		if not ret:
			context.write("No items for key? Did something go wrong?")
			return ''

		items = []
		for item in ret:
			filter = item[2].lower()


			items.append(item)

		trie = build_trie(items, lambda x: x[2])


	%>

	${renderDirectory(trie, '', "item", 0, isBase=True)}

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
					<div class="contentdiv"  style="font-size:20px">
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
	print("Dictinct = ", ret)

	ret = set([item[0].lower() for item in ret])
	%>
	% if len(ret) > 1:
		% for item in ret:
			${lazyTreeNode(rootKey, item)}
		% endfor
	% else:
		${renderWholeBranch(rootKey, treeKey)}
	% endif


</%def>



<%

print("Request params", request.params)


if "url" in request.params:
	url = urllib.parse.unquote(request.params["url"])
	print("Rendering ID", url)
	renderId(url)

elif "tree" in request.params:

	if not "key" in request.params:
		needId()
		return

	key = request.params['key']

	# Require a valid tree key to work.
	if not key in [item[0] for item in settings.bookSources]:
		needId()
		return

	prefix = urllib.parse.unquote(request.params["tree"])
	lazyTreeRender(key, prefix)

else:
	badId()
%>




<%def name="genTrie(inInterable)">
	<%
	return build_trie(inInterable)
	%>

</%def>

