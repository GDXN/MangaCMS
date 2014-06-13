## -*- coding: utf-8 -*-
<!DOCTYPE html>

<%!
import time
import urllib.parse
%>

<html>
<head>
	<title>WAT WAT IN THE BATT</title>
	<link rel="stylesheet" href="style.css">
	<script type="text/javascript" src="/js/jquery-2.1.0.min.js"></script>

	<script type="text/javascript">
		$(document).ready(function() {
		// Tooltip only Text
		$('.showTT').hover(function(){
			// Hover over code
			var title = $(this).attr('title');
			$(this).data('tipText', title).removeAttr('title');
			$('<p class="tooltip"></p>')
			.text(title)
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
<%namespace name="sideBar" file="gensidebar.mako"/>


<%

picked=False
if "picked" in request.params and request.params["picked"] == "True":
	picked=True

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


%>

<body>

<div>

	${sideBar.getSideBar(sqlCon)}
	<div class="maindiv">

		<div class="subdiv mtMainId">
			<div class="contentdiv">
				<h3>MT Series - ${"Picked" if picked else "Not Picked"}${ " - (Only distinct)" if onlyDistinct else ""}</h3>
				<a href="itemsMt?${urllib.parse.urlencode(distinct)}">Distinct series</a> <a href="itemsMt?${urllib.parse.urlencode(nonDistinct)}">All Items</a>
				${tableGenerators.genLegendTable()}
				${tableGenerators.genMangaTable(limit=limit, offset=offset, picked=picked, distinct=onlyDistinct)}
			</div>

			% if pageNo > 0:
				<span class="pageChangeButton" style='float:left;'>
					<a href="itemsMt?${urllib.parse.urlencode(prevPage)}">prev</a>
				</span>
			% endif
			<span class="pageChangeButton" style='float:right;'>
				<a href="itemsMt?${urllib.parse.urlencode(nextPage)}">next</a>
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


