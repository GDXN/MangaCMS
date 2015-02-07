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

	<div class="statusdiv">
		<div class="statediv navId">
			<strong>Navigation:</strong><br />
			<ul>
				<li><a href="/">Index</a>
				<hr>
				<hr>
				<li><a href="/reader2/browse/">Reader</a>
				<hr>
				<li>${randomLink}
				<hr>
				<hr>
				<li><a href="/bmUpdates">Baka Manga</a>
				<hr>
				<li><a href="/books/">Books!</a>
				<li><a href="/books/changeView">New Books</a>
				<hr>
				<li><a href="/itemsManga?distinct=True"><b>All Mangos</b></a>
				<li><a href="/tags/tags">M Tags</a>
				<li><a href="/tags/genres">M Genres</a>
				<li><a href="/rating/">Ratings</a>

				<hr>
				% for item in [item for item in normalPlug]:
					<li><a href="/itemsManga?sourceSite=${item["dictKey"]}&distinct=True">${item["name"]}</a>
				% endfor

				<hr>
				% if utilities.ip_in_whitelist():
					<hr>
					<li><a href="/itemsPron"><b>All Pron</b></a>
					% for item in [item for item in adultPlug]:
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

		<div class="statediv">
			<strong>Status:</strong>
		</div>
		%for plugSet in [normalPlug, adultPlug]:
			% for item in plugSet:

				<div class="statediv ${item['cssClass']}">
					<strong>
						${item["name"]}
					</strong><br />
					% if item['errored']:
						<a href="/errorLog">Had Error!</a><br />
					% endif
					${item['runStart']}<br />
					${item['runState']}

					% if item["dictKey"] != None:
						% if item["dictKey"] in itemCountsDict:
							<%
							keys = [DNLDED, DLING, QUEUED, FAILED]
							pres = [key in itemCountsDict[item["dictKey"]] for key in keys]

							%>
							% if all(pres):
								<ul>
									<li>Have: ${itemCountsDict[item["dictKey"]][DNLDED]}</li>
									<li>DLing: ${itemCountsDict[item["dictKey"]][DLING]}</li>
									<li>Want: ${itemCountsDict[item["dictKey"]][QUEUED]}</li>
									<li>Failed: ${itemCountsDict[item["dictKey"]][FAILED]}</li>
								</ul>
							% endif
						% else:
							<b>WARN: No lookup dict built yet!</b>
						% endif
					% endif

				</div>
			% endfor
		% endfor
	</div>

</%def>
