## -*- coding: utf-8 -*-

<%!
import time
import datetime
from babel.dates import format_timedelta
import os.path
import settings
import string
import urllib.parse
import nameTools as nt


%>


<%namespace name="tableGenerators" file="/gentable.mako"/>
<%namespace name="sideBar"         file="/gensidebar.mako"/>
<%namespace name="ut"              file="/utilities.mako"/>
<%namespace name="ap"              file="/activePlugins.mako"/>


<%def name="getStatsForId(muId)">
	<%
	cur = sqlCon.cursor()
	cur.execute("SELECT readingProgress, availProgress FROM mangaseries WHERE buId=%s;", (muId, ))
	rows = cur.fetchall()
	if not rows or len(rows) != 1:
		print("Wat?")
		return None
	return rows.pop(0)
	%>
</%def>


<%def name="getRatings(thresh=2, sort='alphabetical')">
	<%
	ret = []
	for key, item in nt.dirNameProxy.iteritems():
		if item['fqPath'] == None:
			print("Wat?")
			print(item)
			print(key)
			continue
		item['frating'] = nt.ratingStrToFloat(item['rating'])
		if item['frating'] > thresh:
			ret.append(item)

	if sort == 'alphabetical':
		ret.sort(key=lambda i: i['item'].lower())
	elif sort == 'rating':
		ret.sort(key=lambda i: (i['frating']*-1, i['item'].lower()))
	else:
		raise ValueError("Unknow sort method!")
	return ret
	%>
</%def>


<%def name="genItemRatingTable(rows)">


	<%

	colours = {
		# Download Status
		"hasUnread"       : "FF9999",
		"upToDate"        : "99FF99",
		"notInMT"         : "9999FF",


		"failed"          : "000000",
		"moved"           : "FFFF99",
		"queued"          : "FF77FF",
		"created-dir"     : "FFE4B2",
		"not checked"     : "FFFFFF",

		# Categories

		"valid category"  : "FFFFFF",
		"bad category"    : "999999"}



	%>
	<table border="1px" style="width: 100%;">
		<tr>
				<th class="uncoloured" >Tag</th>
				<th class="uncoloured" style="width: 70px; min-width: 70px;">BuId</th>
				<th class="uncoloured" style="width: 70px; min-width: 70px;">Rating</th>
				<th class="uncoloured" style="width: 70px; min-width: 70px;">Read</th>
				<th class="uncoloured" style="width: 70px; min-width: 70px;">Available</th>
		</tr>

		% for  itemInfo in rows:
			<%

			buId            = nt.getMangaUpdatesId(itemInfo['inKey'].title())
			if buId:
				buName          = nt.getCanonNameByMuId(buId)
				readingProgress, availProgress = getStatsForId(buId)
			else:
				buName          = itemInfo['inKey'].title()
				readingProgress, availProgress = '', ''


			# buName, buId, readingProgress, availProgress  = row
			if not availProgress:
				availProgress = ''
			if not readingProgress:
				readingProgress = ''

			# itemInfo = nt.dirNameProxy[buName]
			%>

			<tr>
				<td>
					${ut.createReaderLink(buName, itemInfo)}
				</td>
				<td>
					${ut.idToLink(buId)}
				</td>
				<td>
					${"" if itemInfo['rating'] == None else itemInfo['rating']}
				</td>


				% if readingProgress == -1:
					% if availProgress == -1:
						<td bgcolor="${colours["upToDate"]}">✓</td>
					% else:
						<td bgcolor="${colours["upToDate"]}">${availProgress}</td>
					% endif

				% elif readingProgress and availProgress and int(readingProgress) < int(availProgress):
					<td bgcolor="${colours["hasUnread"]}">${readingProgress}</td>
				% elif readingProgress:
					<td bgcolor="${colours["upToDate"]}">${readingProgress}</td>
				% else:
					<td >${readingProgress}</td>
				% endif

				% if availProgress == -1 and readingProgress == -1:
					<td>Finished</td>
				% elif availProgress and int(availProgress) > 0:
					<td>${int(availProgress)}</td>
				% elif readingProgress:
					<td>${int(readingProgress)}</td>
				% else:
					<td></td>
				% endif
			</tr>
		% endfor


	</table>
</%def>




<%def name="makeTagLink(tag)">
	<a href='/tags/tag?tag=${tag | u}'>${tag}</a>
</%def>


<%def name="makeGenreLink(genre)">
	<a href='/tags/genre?genre=${genre | u}'>${genre}</a>
</%def>



<%def name="genOptionRow()">

	<%
	letters = string.digits+string.ascii_lowercase


	%>
	<div>
		<div style='float:left'>
			<a href='/rating/'>None</a>
			% for letter in letters:
				<%
				params = request.params.copy();
				params["prefix"] = letter
				url = "/rating/?" + urllib.parse.urlencode(params)
				%>
				<a href='${url}'>${letter.upper()}</a>
			% endfor
		</div>
		<div style='float:right'>

			<%
			params = request.params.copy();
			params["sort"] = 'rating'
			url = "/rating/?" + urllib.parse.urlencode(params)
			%>
			<a href='${url}'>Sort by rating</a>,
			<%
			params = request.params.copy();
			params["sort"] = 'alphabetical'
			url = "/rating/?" + urllib.parse.urlencode(params)
			%>
			<a href='${url}'>Sort Alphabetically</a>
		</div>
	</div>
</%def>

