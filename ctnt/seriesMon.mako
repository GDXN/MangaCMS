## -*- coding: utf-8 -*-

<%startTime = time.time()%>

<%!
import time
import datetime
from babel.dates import format_timedelta
import os.path

import DbManagement.MonitorTool

%>

<%
# print("Req params = ", request.params)

ignoreList=["Good H", "Interesting H", "Meh H"]

if "nofilter" in request.params:
	ignoreList = []

validSortKeys = ["update", "mtName", "buName", "aggregate"]

sortKey = "aggregate"
if "sortBy" in request.params:
	if request.params["sortBy"] in validSortKeys:
		sortKey = request.params["sortBy"]

%>


<%namespace name="tableGenerators" file="gentable.mako"/>
<%namespace name="sideBar" file="gensidebar.mako"/>
<%namespace name="ut" file="utilities.mako"/>


<!DOCTYPE html>
<html>
<head>
	<title>WAT WAT IN THE BATT</title>
	${ut.headerBase()}
	<script type="text/javascript">

		function ajaxSuccess(reqData, statusStr, jqXHR)
		{
			console.log("Ajax request succeeded");
			console.log(reqData);
			console.log(statusStr);
			console.log(jqXHR);
			var text = reqData;
			text = text.replace(/ +/g,' ').replace(/(\r\n|\n|\r)/gm,"");
			window.alert(text);
			// location.reload();

		};
		function ToggleEdit(rowId)
		{
			if ($('#rowid_'+rowId+' #view').is(":visible"))
			{
				$('#rowid_'+rowId+' #view').each(function(){ $(this).hide(); })
				$('#rowid_'+rowId+' #edit').each(function(){ $(this).show(); })
				$('#buttonid_'+rowId).text("Ok")

			}
			else
			{
				$('#rowid_'+rowId+' #view').each(function(){ $(this).show(); })
				$('#rowid_'+rowId+' #edit').each(function(){ $(this).hide(); })
				$('#buttonid_'+rowId).text("Edit")

				var ret = ({});

				$('#rowid_'+rowId+' #edit').map(function()
				{
					var inputF = $(this).find('input:first');
					if (inputF.attr("originalValue") != inputF.val())
					{
						ret["id"] = rowId;
						ret["old_"+inputF.attr('name')] = inputF.attr("originalValue");
						ret["new_"+inputF.attr('name')] = inputF.val();
					}
				});
				if (!$.isEmptyObject(ret))
				{
					ret["update-series"] = true;
					$.ajax("api", {"data": ret, success: ajaxSuccess})
				}
				console.log(ret);

			}
		};


	</script>
</head>


<body>

<div>

	${sideBar.getSideBar(sqlCon)}
	<div class="maindiv">

		<div class="subdiv mtMonId">
			<div class="contentdiv">
				<h3>Monitored Series</h3>
				<div>
				<div style="white-space:nowrap; display: inline-block;">
					%if not "nofilter" in request.params:
						Filtering H lists -<br>
						<a href='seriesMon?nofilter'>disable filter.</a>
					% else:
						Not filtering H lists -<br>
						<a href='seriesMon'>enable filter.</a>
					% endif
				</div>
				<div style="white-space:nowrap; display: inline-block; margin-left: 10px;">
					<ul>
						<li><a href='seriesMon?rated=unrated'>Unrated Only</a></li>
						<li><a href='seriesMon?rated=rated'>Rated Only</a></li>
						<li><a href='seriesMon?rated=all'>All</a></li>
					</ul>
				</div>
				<div style="white-space:nowrap; display: inline-block; margin-left: 10px;">
					<ul>
						<li><a href='seriesMon?sortBy=aggregate'>Aggregate Name</a></li>
						<li><a href='seriesMon?sortBy=update'>Last Update</a></li>
						<li><a href='seriesMon?sortBy=mtName'>MT Name</a></li>
						<li><a href='seriesMon?sortBy=buName'>BU Name</a></li>
					</ul>
				</div>
					${tableGenerators.genMangaSeriesTable(ignoreList=ignoreList, sortKey=sortKey)}
				</div>
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
