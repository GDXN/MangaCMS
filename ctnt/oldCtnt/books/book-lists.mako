## -*- coding: utf-8 -*-
<!DOCTYPE html>


<%namespace name="tableGenerators" file="/gentable.mako"/>
<%namespace name="sideBar"         file="/gensidebar.mako"/>
<%namespace name="ut"              file="/utilities.mako"/>
<%namespace name="ap"              file="/activePlugins.mako"/>
<%namespace name="treeRender"      file="/books/render.mako"/>
<%namespace name="bookRender"       file="/books/book-render.mako"/>

<html>
<head>
	<title>WAT WAT IN THE BATT</title>

	${ut.headerBase()}


	<link rel="stylesheet" href="/books/treeview.css">

</head>


<%
startTime = time.time()
# print("Rendering begun")
%>


<%!
import time
import datetime
from babel.dates import format_timedelta
import os.path
import settings
import traceback
import string

import urllib.parse
%>

<%
startTime = time.time()
# print("Rendering begun")
%>


<%def name="renderList(listName)">

	<%
	bookRender.renderBookList(listName)
	%>
</%def>


<%def name="renderListTable()">
	<%

	cursor = sqlCon.cursor()

	cursor.execute("""SELECT listname FROM book_series_lists ORDER BY listname;""")
	lists = cursor.fetchall()

	%>




	<div>

		% if not lists:
			<tr>
				<td>
					No Lists!
				</td>
			</tr>
		% else:
			<table border="1px">
				<col width="400">
				<tr>
					<th>
						All Lists:
					</th>
				</tr>
				% for list, in lists:
					<tr>
						<td>
							<a href='/books/book-lists?list=${list}'>${list}</a>
						</td>
					</tr>
				% endfor
			</table>
		% endif
	</div>


	<%

	return lists

	%>


</%def>

<%def name="renderListControls()">
	<div>

		<form>
			Create New List:
			<div style="display: inline-block;">
				<input type="text" id="listName", value="" size=50>
			</div>
			<input type="submit" value="Add" class="button">
		</form>
	</div>
	<script>

		function ajaxSuccess(reqData, statusStr, jqXHR)
		{
			console.log("Ajax request succeeded");
			console.log("Content = ", reqData);
			console.log("StatusStr - ", statusStr);
			console.log("jqXHR", jqXHR);
			ctnt = JSON.parse(reqData);
			console.log(ctnt);
			var text = reqData;
			text = text.replace(/ +/g,' ').replace(/(\r\n|\n|\r)/gm,"");
			if (ctnt["Status"] == "Success")
			{
				window.alert("Succeeded!\n"+ctnt["contents"])
				location.reload();
			}
			else
			{
				window.alert("Error!\n"+ctnt["contents"])

			}


		};

		$(function() {
			$(".button").click(function() {

				var inputF = $("#listName").val();

				var ret = ({
					'add-book-list' : true,
					listName : inputF

				});


				$.ajax("/api", {"data": ret, success: ajaxSuccess})


				// validate and process form here
				event.preventDefault();
			});
		});

	</script>
</%def>

<%def name="renderListManagementControls(listName)">
	<%
	cursor = sqlCon.cursor()
	cursor.execute("""SELECT dbid
					FROM book_series_lists
					WHERE listname=%s;""", (listName, ))

	tgtList = cursor.fetchall()

	%>

	% if not tgtList:
		wat
		<%
		return
		%>
	% endif


	<script>

		function itemDeletedCallback(reqData, statusStr, jqXHR)
		{
			console.log("Ajax request succeeded");
			console.log(reqData);
			console.log(statusStr);

			var status = $.parseJSON(reqData);
			console.log(status)
			if (status.Status == "Success")
			{
				window.location.replace("/books/book-lists")
			}
			else
			{
				alert("ERROR!\n"+status.contents)
			}

		};
		function deleteListItem(newList)
		{


			var ret = ({});
			ret["remove-book-list"] = true;
			ret["listName"] = '${listName}';

			var confirm = window.confirm("Are you sure you want to delete the list named '${listName}'?");

			if (confirm == true)
			{
				$.ajax("/api", {"data": ret, success: itemDeletedCallback});
			}

		}
	</script>

	<div class="lightRect itemInfoBox">
		Delete this list:
		<button onclick="deleteListItem()">Delete</button>
	</div>
</%def>

<%def name="renderAllLists()">
	<h2>Book Lists</h2>
	<%
	renderListControls()
	lists = renderListTable()


	%>
	<hr>
	% for list, in lists:
		<div>
			<br>
			<strong>List: ${list}</strong>
			<%
			renderList(list)
			%>
		</div>
	% endfor
</%def>




<%
listName = ut.getUrlParam('list')
%>

<body>


	<div>
		${sideBar.getSideBar(sqlCon)}
		<div class="maindiv">

			<div class="subdiv">
				<div class="contentdiv">
					% if listName:
						<h2>List: ${listName}</h2>
						<%
						renderList(listName)
						renderListManagementControls(listName)
						%>
					% else:
						<% renderAllLists() %>
					% endif


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