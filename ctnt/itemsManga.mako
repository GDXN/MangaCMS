## -*- coding: utf-8 -*-
<!DOCTYPE html>

<%!
import time
import urllib.parse
%>

<%namespace name="ut"              file="utilities.mako"/>
<html>
<head>
	<title>WAT WAT IN THE BATT</title>
	${ut.getCss()}
	<script type="text/javascript" src="/js/jquery-2.1.0.min.js"></script>

	<script type="text/javascript">
		$(document).ready(function() {
		// Tooltip only Text
		$('.showTT').hover(function(){
			// Hover over code
			var title = $(this).attr('title');
			$(this).data('tipText', title).removeAttr('title');
			$('<p class="tooltip"></p>')
			.html(title)
			.appendTo('body')
			.fadeIn('slow');
		}, function() {
			// Hover out code
			$(this).attr('title', $(this).data('tipText'));
			$('.tooltip').remove();
		}).mousemove(function(e) {
			var mousex = e.pageX + 20; //Get X coordinates
			var mousey = e.pageY + 10; //Get Y coordinates
			$('.tooltip')
			.css({ top: mousey, left: mousex })
		});
		});
	</script>

</head>

<%startTime = time.time()%>

<%namespace name="tableGenerators" file="gentable.mako"/>
<%namespace name="sideBar"         file="gensidebar.mako"/>
<%namespace name="ap"              file="activePlugins.mako"/>


<%


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

distinct = request.params.copy();
distinct["distinct"] = True

nonDistinct = request.params.copy();
nonDistinct["distinct"] = False

if "distinct" in request.params and request.params["distinct"] == "True":
	print("Distinct")
	onlyDistinct = True
else:
	onlyDistinct = False




if "sourceSite" in request.params:
	tmpSource = request.params.getall("sourceSite")
	sourceFilter = [item for item in tmpSource if item in ap.attr.activeNonPorn]
else:
	sourceFilter = []

print("sourceFilter", sourceFilter)
if len(sourceFilter) > 1:
	divId      = "skId"
	sourceName = 'Manga Series'
elif sourceFilter == ["mt"]:
	divId      = "mtMainId"
	sourceName = 'MT Series'
elif sourceFilter == ["sk"]:
	divId      = "skId"
	sourceName = 'Starkana Series'
elif sourceFilter == ["cz"]:
	divId      = "czId"
	sourceName = 'Crazy\'s Manga Series'
elif sourceFilter == ["mb"]:
	divId      = "mbId"
	sourceName = 'MangaBaby Series'
elif sourceFilter == ["jz"]:
	divId      = "jzId"
	sourceName = 'Japanzai Series'
elif sourceFilter == ["bt"]:
	divId      = "btId"
	sourceName = 'Batoto Series'
elif sourceFilter == ["mk"]:
	divId      = "mkId"
	sourceName = 'Manga.Madokami Series'
elif sourceFilter == ["mc"]:
	divId      = "mcId"
	sourceName = 'Manga Cow Series'
else:
	sourceFilter = None
	divId      = ""
	sourceName = 'ALL DEM ITEMZ?'



%>

<body>

<div>

	${sideBar.getSideBar(sqlCon)}
	<div class="maindiv">
		<div class="subdiv ${divId}">

				<div class="contentdiv">
					<h3>${sourceName}${ " - (Only distinct)" if onlyDistinct else ""}</h3>
					<a href="itemsManga?${urllib.parse.urlencode(distinct)}">Distinct series</a> <a href="itemsManga?${urllib.parse.urlencode(nonDistinct)}">All Items</a>
					${tableGenerators.genLegendTable()}
					${tableGenerators.genMangaTable(tableKey=sourceFilter, limit=limit, offset=offset, distinct=onlyDistinct)}
				</div>

				% if pageNo > 0:
					<span class="pageChangeButton" style='float:left;'>
						<a href="itemsManga?${urllib.parse.urlencode(prevPage)}">prev</a>
					</span>
				% endif
				<span class="pageChangeButton" style='float:right;'>
					<a href="itemsManga?${urllib.parse.urlencode(nextPage)}">next</a>
				</span>

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


