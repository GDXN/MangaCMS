## -*- coding: utf-8 -*-
<!DOCTYPE html>
<%startTime = time.time()%>

<%namespace name="tableGenerators" file="/gentable.mako"/>
<%namespace name="sideBar"         file="/gensidebar.mako"/>
<%namespace name="ut"              file="/utilities.mako"/>
<%namespace name="genericFuncs"        file="/tags/genericFuncs.mako"/>


<%!
# Module level!
import time
import datetime
from babel.dates import format_timedelta
import os.path
import os


from natsort import natsorted
import magic
from operator import itemgetter

import nameTools as nt
import unicodedata
import traceback
import settings
import urllib.parse
import uuid

styles = ["skId", "mtMonId", "czId", "mbId", "djMoeId", "navId"]

def dequoteDict(inDict):
	ret = {}
	for key in inDict.keys():
		ret[key] = urllib.parse.unquote_plus(inDict[key])
	return ret

%>


<%def name="renderHTablesForBuId(buId)">
	<%
	# Short circuit if we don't have anything to render.
	if not buId:
		return
	if not ut.ip_in_whitelist():
		return


	names = nt.buSynonymsLookup[buId]
	names.sort()
	#
	%>
	<hr>
	<div>
		<div>
			<b>Related Hentai Searches</b>
		</div>
		% for name in names:
			<%
			itemId = uuid.uuid4().hex
			%>

			<script type="text/javascript">
				$(document).ready(function() {

					$.get("/search-h/hs?q=${name | u}",
						function( response, status, xhr )
						{
							if ( status == "error" )
							{
								var msg = "Sorry but there was an error: ";
								$( "#${itemId}" ).html( msg + xhr.status + " " + xhr.statusText );
							}
							else
							{
								$('#${itemId}').html(response);
							}
						}
					);

				});

			</script>



			Name: ${name}
			<div id='${itemId}'>
				<center><img src='/js/loading.gif' /></center>
			</div>
		% endfor
	</div>
</%def>


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
			${ut.getCss()}
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

			<a href="/reader2/browse/">Back</a>
		</div>

	</div>

</%def>



<%def name="badFileError(itemPath)">

	<html>
		<head>
			<title>WAT WAT IN THE READER</title>
			${ut.getCss()}
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
							<p>Magic file-type = ${magic.from_file(itemPath)}</p>
							<p>File path:<pre>${itemPath}</pre></p>
						</div>
						<a href="/reader2/browse/">Back</a>
					</div>
				</div>
			<div>

		</body>
	</html>

</%def>




<%def name="showMangaItems(itemPath)">

	<%

	if not (os.path.isfile(itemPath) and os.access(itemPath, os.R_OK)):

		invalidKey(title="Trying to read file that does not exist!")
		return



	try:
		# We have a valid file-path. Read it!
		sessionArchTool.checkOpenArchive(itemPath)
		keys = sessionArchTool.getKeys()  # Keys are already sorted


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
					"fileName":"${itemPath.split("/")[-1]}"
				});

				book.draw();

				$(window).on('resize', function () {
					book.draw();
				});
			</script>
		</body>
	</html>


</%def>



<%def name="generateInfoSidebar(itemDict)">


	<%

	if not itemDict["item"]:
		return

	fullPath = itemDict['fqPath']
	baseName = fullPath.split("/")[-1]



	# itemTemp = nt.dirNameProxy.getRawDirDict(pathKey)
	# keys = list(itemTemp.keys())
	# keys.sort()


	name = nt.sanitizeString(itemDict["item"], flatten=False)
	buId, haveBu, buLink, buTags, buGenre, buList, readProgress, availProgress = ut.getItemInfo(name)




	if haveBu:
		haveBu = "✓"
	else:
		haveBu = "✗"



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
				$('#rating-status').html("✓");
				location.reload();
			}
			else
			{
				$('#rating-status').html("✗");
				alert("ERROR!\n"+status.Message)
			}

		};
		function ratingChange(newRating)
		{
			$('#rating-status').html("❍");

			var ret = ({});
			ret["change-rating"] = "${itemDict["dirKey"]}";
			ret["new-rating"] = newRating;
			$.ajax("/api", {"data": ret, success: ajaxCallback});
			// alert("New value - "+newRating);
		}
	</script>


	<div class="readerInfo" id="searchDiv">

		<div class="lightRect itemInfoBox">
			 ${baseName}
		</div>

		<div class="lightRect itemInfoBox">
			 Cleaned = '${nt.prepFilenameForMatching(baseName)}'
		</div>


		<div class="lightRect itemInfoBox">
			 MangaUpdates ID = ${nt.getMangaUpdatesId(baseName)}
		</div>


		<div class="lightRect itemInfoBox">
			${haveBu} ${buLink}
			<form method="post" action="http://www.mangaupdates.com/series.html" id="muSearchForm" target="_blank">
				<input type="hidden" name="act" value="series"/>
				<input type="hidden" name="session" value=""/>
				<input type="hidden" name="stype" value="Title">
				<input type="hidden" name="search" value="${itemDict["dirKey"] | h}"/>

			</form>
		</div>
		<div class="lightRect itemInfoBox">
			Rating<br>
			<%
			rtng = itemDict["rating"]
			# print("Item rating = ", rtng)
			%>
			<select name="rating" id="rating" onchange="ratingChange(this.value)">
				<option value="-1"   ${"selected='selected''" if rtng == "-"     else ""}>-     </option>
				<option value="0"    ${"selected='selected''" if rtng == ""      else ""}>NR    </option>
				<option value="0.5"  ${"selected='selected''" if rtng == "~"     else ""}>~     </option>
				<option value="1"    ${"selected='selected''" if rtng == "+"     else ""}>+     </option>
				<option value="1.5"  ${"selected='selected''" if rtng == "+~"    else ""}>+~    </option>
				<option value="2"    ${"selected='selected''" if rtng == "++"    else ""}>++    </option>
				<option value="2.5"  ${"selected='selected''" if rtng == "++~"   else ""}>++~   </option>
				<option value="3"    ${"selected='selected''" if rtng == "+++"   else ""}>+++   </option>
				<option value="3.5"  ${"selected='selected''" if rtng == "+++~"  else ""}>+++~  </option>
				<option value="4"    ${"selected='selected''" if rtng == "++++"  else ""}>++++  </option>
				<option value="4.5"  ${"selected='selected''" if rtng == "++++~" else ""}>++++~ </option>
				<option value="5"    ${"selected='selected''" if rtng == "+++++" else ""}>+++++ </option>
			</select>
			<span id="rating-status">✓</span>
		</div>

		% if readProgress:
			<div class="lightRect itemInfoBox">
			% if readProgress >= 0:
				% if availProgress > 0:
					% if readProgress != availProgress:
						<b>Unread Chapters!</b><br>
					% endif
					Read ${readProgress} of ${availProgress} chapters.

				% else:
					Read ${readProgress} chapters.

				% endif
			% else:
				Manga Finished!

			% endif
			</div>
		% endif

		% if buList:
			<div class="lightRect itemInfoBox">
				Bu List: ${buList}
			</div>
		% else:
			<div class="lightRect itemInfoBox">
				Not in any MangaUpdates list
			</div>
		% endif

		% if buTags:
			<div class="lightRect itemInfoBox">

				Bu Tags:
				<ul>
					<%
					if not buTags:
						buTags = ""

					tags = buTags.split(" ")
					tags.sort()
					%>
					% for item in tags:
						<li>${genericFuncs.makeTagLink(item)}</li>
					% endfor
				</ul>
			</div>
		% endif

		% if buGenre:
			<div class="lightRect itemInfoBox">
				Bu Genre:

				% for item in buGenre.split():
					${genericFuncs.makeGenreLink(item)}
				% endfor
			</div>
		% endif


		% if buId:

			<div class="lightRect itemInfoBox">
				Other names:
				<%
				names = nt.buSynonymsLookup[buId]
				%>
				<ul>
					% for name in names:
						<li>${name}</li>
					% endfor

				</ul>
			</div>

		% endif


	</div>

	<%
	return buId
	%>

</%def>

