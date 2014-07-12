## -*- coding: utf-8 -*-
<!DOCTYPE html>
<%startTime = time.time()%>

<%namespace name="tableGenerators" file="/gentable.mako"/>
<%namespace name="sideBar" file="/gensidebar.mako"/>

<%namespace name="ut"              file="/utilities.mako"/>

<%!
# Module level!
import time
import datetime
from babel.dates import format_timedelta
import os.path
import os


import magic
from operator import itemgetter

import nameTools as nt
import unicodedata
import traceback
import settings
import urllib.parse

styles = ["mtMainId", "mtSubId", "djMoeId", "fuFuId"]

def dequoteDict(inDict):
	ret = {}
	for key in inDict.keys():
		ret[key] = urllib.parse.unquote_plus(inDict[key])
	return ret

%>



<%def name="readerBrowseHeader()">

	<html>
		<head>
			<title>WAT WAT IN THE READER</title>
			${ut.headerBase()}

		</head>



		<body>


			<div>
				${sideBar.getSideBar(sqlCon)}
				<div class="maindiv">

</%def>


<%def name="readerBrowseFooter()">


				</div>
			<div>

			<%
			stopTime = time.time()
			timeDelta = stopTime - startTime
			%>

			<p>This page rendered in ${timeDelta} seconds.</p>

		</body>
	</html>
</%def>





<%def name="invalidKey(title='Error', message=None)">

	<html>
		<head>
			<title>WAT WAT IN THE READER</title>
			<link rel="stylesheet" href="/style.css">
			<script type="text/javascript" src="/js/jquery-2.1.0.min.js"></script>

		</head>



		<body>


			<div>
				${sideBar.getSideBar(sqlCon)}
				<div class="maindiv">
					${invalidKeyContent(title, message)}
				</div>
			<div>

		</body>
	</html>


</%def>



<%def name="invalidKeyContent(title='Error', message=None)">

	<div class="contentdiv subdiv uncoloured">
		<h3>${title}</h3>
		<div class="errorPattern">
			% if message == None:
				<h3>Invalid Manga file specified!</h3>
			% else:
				<h3>${message}</h3>
			% endif

			Are you trying to do something naughty?<br>

			<pre>MatchDict = ${request.matchdict}</pre>
			<pre>URI = ${request.path}</pre>

			<a href="/reader/">Back</a>
		</div>

	</div>

</%def>



<%def name="badFileError(itemPath)">

	<html>
		<head>
			<title>WAT WAT IN THE READER</title>
			<link rel="stylesheet" href="/style.css">
			<script type="text/javascript" src="/js/jquery-2.1.0.min.js"></script>

		</head>

		<body>


			<div>
				${sideBar.getSideBar(sqlCon)}
				<div class="maindiv">
					<div class="contentdiv subdiv uncoloured">
						<h3>Reader!</h3>

						<div class="errorPattern">
							<h3>Specified file is damaged?</h3>
							<pre>${traceback.format_exc()}</pre><br>
						</div>

						<div class="errorPattern">
							<h3>File info:</h3>
							<p>Exists = ${os.path.exists(itemPath)}</p>
							<p>Magic file-type = ${magic.from_file(itemPath).decode()}</p>
						</div>
						<a href="/reader/">Back</a>
					</div>
				</div>
			<div>

		</body>
	</html>

</%def>




<%def name="showMangaItems(itemPath)">

	<%

	if not (os.path.isfile(itemPath) and os.access(itemPath, os.R_OK)):
		print("")
		invalidKey(title="Trying to read file that does not exist!")
		return



	try:
		# We have a valid file-path. Read it!
		sessionArchTool.checkOpenArchive(itemPath)
		print("sessionArchTool", sessionArchTool)
		keys = sessionArchTool.getKeys()  # Keys are already sorted

		print("Items in archive", keys)
		print("Items in archive", sessionArchTool.items)

		keyUrls = []
		for indice in range(len(keys)):
			keyUrls.append("'/reader2/file/%s'" % (indice))


	except:
		print("Bad file")
		badFileError(itemPath)
		return

	%>

	<html style='html: -ms-content-zooming: none; /* Disables zooming */'>
		<head>
			<meta charset="utf8">
			<meta name="viewport" content="width=device-width; initial-scale=1.0; maximum-scale=1.0; user-scalable=0; width=device-width;">

			<meta name="mobile-web-app-capable" content="yes">
			<meta name="apple-mobile-web-app-capable" content="yes">
			<meta name="apple-mobile-web-app-status-bar-style" content="black">

			<title>Reader (${itemPath.split("/")[-1]})</title>

			<script src="/js/jquery-2.1.1.js"></script>
			<script src="/comicbook/js/comicbook.js"></script>
			<link rel="stylesheet" href="/nozoom.css">
			<link rel="stylesheet" href="/comicbook/comicbook.css">
			<link rel="shortcut icon" sizes="196x196" href="/comicbook/img/icon_196.png">
			<link rel="apple-touch-icon" sizes="196x196" href="/comicbook/img/icon_196.png">
			<link rel="apple-touch-icon-precomposed" sizes="196x196" href="/comicbook/img/icon_196.png">


		</head>
		<body>
			<div style="line-height: 0;" id="canvas_container"></div>
			<!-- <div id="canvas_container"></div> -->
			<!-- <canvas id="comic"></canvas> -->


			<script>

				var book = new ComicBook('canvas_container', [


					${", ".join(keyUrls)}


				], {

				});

				book.draw();

				$(window).on('resize', function () {
					book.draw();
				});
			</script>
		</body>
	</html>


</%def>




<%def name="generateInfoSidebar(filePath, keyUrls)">


	<div class="readerInfo" id="searchDiv">

		<div class="lightRect itemInfoBox">
			 ${baseName}
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
			# print("Item rating = ", rtng)
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

		% if buId:

			<div class="lightRect itemInfoBox">
				Other names:
				<%
				print(buId)
				names = nt.buSynonymsLookup[buId]
				print(names)
				%>
				<ul>
					% for name in names:
						<li>${name}</li>
					% endfor

				</ul>
			</div>

		% endif


	</div>



</%def>

