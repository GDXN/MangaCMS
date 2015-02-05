## -*- coding: utf-8 -*-
<!DOCTYPE html>



<%!
import time
import datetime
from babel.dates import format_timedelta
import os.path
import settings
import string
import urllib.parse
%>


<%namespace name="tableGenerators" file="/gentable.mako"/>
<%namespace name="sideBar"         file="/gensidebar.mako"/>
<%namespace name="ut"              file="/utilities.mako"/>
<%namespace name="ap"              file="/activePlugins.mako"/>
<%namespace name="rtngFuncs"        file="/rating/ratingFuncs.mako"/>

<html>
<head>
	<title>WAT WAT IN THE BATT</title>

	${ut.headerBase()}

</head>



<%
startTime = time.time()
# print("Rendering begun")

if "sort" in request.params and request.params["sort"] == "rating":
	sort = 'rating'
else:
	sort = 'alphabetical'


thresh = 2
rows = rtngFuncs.getRatings(thresh=thresh, sort=sort)

%>

<body>


<div>
	${sideBar.getSideBar(sqlCon)}
	<div class="maindiv">

		<div class="subdiv skId">
			<div class="contentdiv">
				<h3>Manga Ratings!</h3>
				${rtngFuncs.genOptionRow()}
				<div id='mangatable'>
					% if not rows:
						<div class='errorPattern'>
							<p>No items for rating threshold '${thresh}'</p>
						</div>
					% else:
						${rtngFuncs.genItemRatingTable(rows)}
					% endif
				</div>
			</div>
		</div>

	</div>
</div>


<%
fsInfo = os.statvfs(settings.mangaFolders[1]["dir"])
stopTime = time.time()
timeDelta = stopTime - startTime
%>

<p>
	This page rendered in ${timeDelta} seconds.<br>
	Disk = ${int((fsInfo.f_bsize*fsInfo.f_bavail) / (1024*1024))/1000.0} GB of  ${int((fsInfo.f_bsize*fsInfo.f_blocks) / (1024*1024))/1000.0} GB Free.
</p>

</body>
</html>