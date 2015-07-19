## -*- coding: utf-8 -*-
<!DOCTYPE html>
<%!
# Module level!

import time



import statusManager as sm
import nameTools as nt

FAILED = -1
QUEUED = 0
DLING  = 1
DNLDED = 2

%>
<%namespace name="sidebar"   file="/model/sidebar.mako"/>
<%namespace name="utilities" file="/model/utilities.mako"/>
<%namespace name="ap"        file="/model/activePlugins.mako"/>


<%def name="getSideBar(sqlConnection)">

	<%

	itemCountsDict  = sidebar.fetchSidebarCounts(sqlConnection)
	normalPlug, adultPlug = sidebar.fetchSidebarPluginStatus(sqlConnection)

	randomLink      = sidebar.fetchRandomLink()


	%>

	<div class="statediv navId">
		<div class="statusdiv">
			<strong>Navigation:</strong><br />
			<ul>
				<li><a href="/m/">Index</a>

				<hr>
				<li><strong>Eastern</strong></a>
				<li><a href="/m/books/">Books!</a>
				<li><a href="/m/books/change_view">New Books</a>
				<li><a href="/m/books/search">Book Search</a>
				<li><a href="/m/books/all">All books</a>
				<hr>
				<li><strong>Western</strong></a>
				<li><a href="/m/books-w/">Books!</a>
				<li><a href="/m/books-w/changeView">New Books</a>
				<li><a href="/m/books-w/search">Book Search</a>
				<li><a href="/m/books-w/book-sources?src=books_custom">Custom</a>
				<hr>
				## <li><a href="/m/itemsManga?distinct=True"><b>All Mangos</b></a>
				## <li><a href="/m/tags/tags">M Tags</a>
				## <li><a href="/m/tags/genres">M Genres</a>
				## <li><a href="/m/rating/">Ratings</a>

				## <hr>
				## % for item in [item for item in normalPlug]:
				## 	<li><a href="/m/itemsManga?sourceSite=${item["dictKey"]}&distinct=True">${item["name"]}</a>
				## % endfor

				## <hr>
				## % if adultPlug:
				## 	<hr>
				## 	<li><a href="/m/itemsPron"><b>All Pron</b></a>
				## 	% for item in [item for item in adultPlug]:
				## 		<li><a href="/m/itemsPron?sourceSite=${item["dictKey"]}">${item["name"]}</a>
				## 	% endfor
				## 	<hr>
				## 	<li><a href="/m/hTags">H Tags</a>
				## 	<hr>
				## 	<hr>
				## 	<li><a href="/m/hentaiError">H Errors</a>
				## % endif
				## <li><a href="/m/mangaError">M Errors</a>
				## <hr>
				## <li><a href="/m/dbg/">Debug Tools</a>
				## <li><a href="/m/errorLog">Scraper Logs</a>


			</ul>
		</div>
		<br>

	</div>

</%def>
