## -*- coding: utf-8 -*-
<!DOCTYPE html>

<%!
import time
import urllib.parse
%>

<%startTime = time.time()%>

<%namespace name="sideBar"         file="gensidebar.mako"/>
<%namespace name="ut"              file="utilities.mako"/>






<%
import pprint

def insert(inDict, item):
	if not inDict:
		return
	path = item.pop(0)
	if not path in inDict:
		inDict[path] = {}
	insert(inDict[path], item)

def buildTrie(inList):
	trieDict = {}
	for path in inList:
		floating_dict = trieDict
		for segment in path:
			floating_dict = floating_dict.setdefault(segment, {})

	return trieDict

def getDistinct():


	with sqlCon.cursor() as cur:
		cur.execute("BEGIN;")
		cur.execute("SELECT DISTINCT(source) FROM logtable;")
		ret = cur.fetchall()
		cur.execute("COMMIT;")

	vals = []
	for item in ret:
		item = item[0]
		if ".Thread-" in item:
			item = item.split(".Thread-")[0]
		if item.startswith("Main.Main."):
			item = item[5:]
		if item.endswith(".Run"):
			item = item[:-4]

		item = item.split(".")
		if not item in vals:
			vals.append(item)
	vals.sort()
	return vals



limit = 200
pageNo = 0


if "page" in request.params:
	try:
		pageNo = int(request.params["page"])-1
	except ValueError:
		pass

if pageNo < 0:
	pageNo = 0

offset = limit * pageNo


prevPage = request.params.copy();
prevPage["page"] = pageNo
nextPage = request.params.copy();
nextPage["page"] = pageNo+2

if "logPrefix" in request.params:
	logPrefix = request.params["logPrefix"]
else:
	logPrefix = None

if "errLevel" in request.params:
	errLevel = request.params["errLevel"]
else:
	errLevel = 30

%>





<%def name="renderTrie(path, trie, base=False)">
	<%
	if not trie:
		return
	keys = list(trie.keys())
	keys.sort()

	%>
	<ul ${'' if not base else "class='colums'"}>
	% for key in keys:
		<%
		curPath = path+[key]
		%>
		<li>
			<div id='rowLink'><a href='/errorLog?logPrefix=${urllib.parse.quote(".".join(curPath))}'>${".".join(curPath)}</a></div>
		</li>
		% if trie[key]:
			${renderTrie(curPath, trie[key])}
		% endif
	% endfor
	</ul>
</%def>




<%def name="genLoggerPathList()">
	<%
	distinct = getDistinct()
	trie = buildTrie(distinct)
	%>
	<div>
		${renderTrie([], trie, base=True)}
	</div>


</%def>

<%def name="genRow(row)">
	<%
	retreivalTime, source, level, content = row
	retreivalTime = time.strftime('%y-%m-%d %H:%M', time.localtime(retreivalTime))

	if ".Thread-" in source:
		source = source.split(".Thread-")[0]
	content = content.replace("\n", "<br>")
	content = content.replace("\t", "&nbsp;&nbsp;&nbsp;&nbsp;")
	%>
	<tr>
		<td>
			${retreivalTime}
		</td>
		<td>
			${source}
		</td>
		<td>
			${level}
		</td>
		<td>
			<div class='preformat level-${level}'>
				${content}
			</div>
		</td>

	</tr>
</%def>

<%def name="genErrorTable(logPrefix, level=0)">
	<%
	with sqlCon.cursor() as cur:
		cur.execute("BEGIN;")

		params = (logPrefix+"%", level, limit, offset)
		cur.execute("""SELECT time,
								source,
								level,
								content
						FROM logTable
						WHERE
							source LIKE %s AND
							level >= %s
						ORDER BY time DESC
						LIMIT %s OFFSET %s
						;""", params)
		ret = cur.fetchall()
		cur.execute("COMMIT;")


	%>
	<table>

		<tr>
				<th class="uncoloured" style="width: 101px; min-width: 101px;">Date</th>
				<th class="uncoloured" style="width: 120px; min-width: 120px;">Path</th>
				<th class="uncoloured" style="width: 20px; min-width: 20px;">Lvl</th>
				<th class="uncoloured">Message</th>
		</tr>

		% for row in ret:
			${genRow(row)}
		% endfor
	</table>


</%def>


<%def name="errThreshDiv()">
	<%

	info     = request.params.copy()
	warn     = request.params.copy()
	err      = request.params.copy()
	critical = request.params.copy()

	info["errLevel"]     = 20
	warn["errLevel"]     = 30
	err["errLevel"]      = 40
	critical["errLevel"] = 50

	%>
	<div>
		<ul class='colums'>
			<li class='columns'> <a href="errorLog?${urllib.parse.urlencode(info)}">Info</a></li>
			<li class='columns'> <a href="errorLog?${urllib.parse.urlencode(warn)}">Warning</a></li>
			<li class='columns'> <a href="errorLog?${urllib.parse.urlencode(err)}">Error</a></li>
			<li class='columns'> <a href="errorLog?${urllib.parse.urlencode(critical)}">Critical</a></li>
		</ul>
	</div>

</%def>





<html>
	<head>
		<title>WAT WAT IN THE BATT</title>
		${ut.headerBase()}

		<style>
		ul.colums
		{
			-moz-column-count: 4;
			-moz-column-gap: 20px;
			-webkit-column-count: 4;
			-webkit-column-gap: 20px;
			column-count: 4;
			column-gap: 20px;



			list-style-type: square;
			margin-left: 10px;
			margin-top: 10px;
			margin-right: 10px;
			margin-bottom: 10px;

			padding-left: 10px;
			padding-top: 10px;
			padding-right: 10px;
			padding-bottom: 10px;


		}

		li.columns  /* Space out list items */
		{
			margin: 5px 5px 5px 5px;
		}



		div.preformat
		{
			font-family: Courier;
		}

		div.level-10
		{
			color: grey;
		}
		div.level-20
		{

		}
		div.level-30
		{
			font-weight: bold;
		}
		div.level-40
		{
			font-weight: bold;
			color: red;
		}
		div.level-50
		{
			background-color: black;
			font-weight: bold;
			color: red;
		}


		#wrapper table
		{
			width: 100%;
		}
		td
		{
			!important word-wrap: break-word;
		}
		</style>

	</head>
	<body>

		<div>

			${sideBar.getSideBar(sqlCon)}
			<div class="maindiv">
				<div class="subdiv" id="wrapper">

						<div class="contentdiv">
							<h3>Error Logs!</h3>

						</div>

						% if logPrefix:
							${errThreshDiv()}
							${genErrorTable(logPrefix, errLevel)}
							% if pageNo > 0:
								<span class="pageChangeButton" style='float:left;'>
									<a href="errorLog?${urllib.parse.urlencode(prevPage)}">prev</a>
								</span>
							% endif
							<span class="pageChangeButton" style='float:right;'>
								<a href="errorLog?${urllib.parse.urlencode(nextPage)}">next</a>
							</span>
						% endif


				</div>

				<div class="subdiv Sources">

					<div style='padding-left: 10px;'>
						<h4>Logger Paths</h4>
					</div>
					<div class="contentdiv">
						${genLoggerPathList()}
					</div>
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


