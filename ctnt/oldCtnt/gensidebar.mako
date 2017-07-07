## -*- coding: utf-8 -*-
<!DOCTYPE html>
<%!
# Module level!

import time
import datetime
from babel.dates import format_timedelta

import statusManager as sm
import nameTools as nt


%>

<%namespace name="ut" file="utilities.mako"/>
<%namespace name="ap" file="activePlugins.mako"/>


<%def name="getSideBar(sqlConnection)">

	<%
	try:
		randomLink = ut.createReaderLink("Random", nt.dirNameProxy.random())
	except ValueError:
		randomLink = "Not Available"
	%>

	<div class="statediv navId">
		<div class="statusdiv">
			<strong>Navigation:</strong><br />
			<ul>
				<li><a href="/">Index</a>
				<li><a href="/status">Status</a>
				<hr>
				<hr>
				<li><a href="/reader2/browse/">Reader</a>
				<hr>
				<li>${randomLink}
				<hr>
				<hr>
				<li><a href="/bmUpdates">Baka Manga</a>
				<li><a href="/books/book-lists">Book Lists</a>
				<li><a href="/books/book-sources">Book Titles</a>
				<li><a href="/feeds/">Book RSS</a>
				<hr>
				<li><strong>Eastern</strong></a>
				<li><a href="/books/">Books!</a>
				<li><a href="/books/changeView">New Books</a>
				<li><a href="/books/search">Book Search</a>
				<li><a href="/books/book-sources?src=books_lndb">LNDB</a>
				<li><a href="/books/book-sources?src=books_custom">Custom</a>
				<li><a href="/books/book-sources?src=MangaSeries">MU Books</a>
				<hr>
				<li><strong>Western</strong></a>
				<li><a href="/books-w/">Books!</a>
				<li><a href="/books-w/changeView">New Books</a>
				<li><a href="/books-w/search">Book Search</a>
				<li><a href="/books-w/book-sources?src=books_custom">Custom</a>
				<hr>
				<li><a href="/itemsManga?distinct=True"><b>All Mangos</b></a>
				<li><a href="/tags/tags">M Tags</a>
				<li><a href="/tags/genres">M Genres</a>
				<li><a href="/rating/">Ratings</a>

				<hr>
				% for item in [item for item in ap.attr.sidebarItemList if item['type'] == "Manga"]:
					<li><a href="/itemsManga?sourceSite=${item["dictKey"]}&distinct=True">${item["name"]}</a>
				% endfor

				<hr>
				% if ut.ip_in_whitelist():
					<hr>
					<li><a href="/itemsPron"><b>All Pron</b></a>
					% for item in [item for item in ap.attr.sidebarItemList if item['type'] == "Porn"]:
						<li><a href="/itemsPron?sourceSite=${item["dictKey"]}">${item["name"]}</a>
					% endfor
					<hr>
					<li><a href="/hTags">H Tags</a>
					<hr>
					<hr>
					<li><a href="/hentaiError">H Errors</a>
				% endif
				<li><a href="/mangaError">M Errors</a>
				<hr>
				<li><a href="/dbg/">Debug Tools</a>
				<li><a href="/errorLog">Scraper Logs</a>


			</ul>
		</div>
		<br>

	</div>

</%def>
