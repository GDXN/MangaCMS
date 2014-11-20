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


<%def name="getAllTags(letterPrefix=None, alphabetize=True)">
	<%

	cur = sqlCon.cursor()
	if alphabetize:
		sort = 'word ASC'
	else:
		sort = 'nentry DESC'

	cur.execute("SELECT word, nentry FROM ts_stat('SELECT buTags::tsvector from mangaseries') ORDER BY {sort};".format(sort=sort))
	tags = cur.fetchall()

	if letterPrefix:
		tags = [tag for tag in tags if tag[0].lower().startswith(letterPrefix.lower())]

	return tags

	%>
</%def>

<%def name="getAllGenres(letterPrefix=None, alphabetize=True)">
	<%

	cur = sqlCon.cursor()
	if alphabetize:
		sort = 'word ASC'
	else:
		sort = 'nentry DESC'

	cur.execute("SELECT word, nentry FROM ts_stat('SELECT buGenre::tsvector from mangaseries') ORDER BY {sort};".format(sort=sort))
	tags = cur.fetchall()

	if letterPrefix:
		tags = [tag for tag in tags if tag[0].lower().startswith(letterPrefix.lower())]

	return tags

	%>
</%def>



<%def name="getSeriesForTag(tag)">
	<%
	cur = sqlCon.cursor()
	cur.execute("SELECT buName, buId, readingProgress, availProgress FROM mangaseries WHERE %s::tsquery @@ lower(butags)::tsvector ORDER BY buName ASC;", (tag.lower(), ))
	rows = cur.fetchall()
	return rows
	%>
</%def>
<%def name="getSeriesForGenre(genre)">
	<%
	cur = sqlCon.cursor()
	cur.execute("SELECT buName, buId, readingProgress, availProgress FROM mangaseries WHERE %s::tsquery @@ lower(buGenre)::tsvector ORDER BY buName ASC;", (genre.lower(), ))
	rows = cur.fetchall()
	return rows
	%>
</%def>

<%def name="genTableForTag(tag=None, genre=None)">
	<%

	if tag:
		rows = getSeriesForTag(tag)
	elif genre:
		rows = getSeriesForGenre(genre)
	else:
		print(tag, genre)
		return genTagError(errStr="No tag specified to table generator!")

	genMatchingKeyTable(rows)

	%>
</%def>



<%def name="genMatchingKeyTable(rows)">


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

		% for  buName, buId, readingProgress, availProgress  in rows:
			<%
			if not availProgress:
				availProgress = ''
			if not readingProgress:
				readingProgress = ''

			itemInfo = nt.dirNameProxy[buName]
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
						<td bgcolor="${colours["upToDate"]}" class="padded">✓</td>
					% else:
						<td bgcolor="${colours["upToDate"]}" class="padded">${availProgress}</td>
					% endif
				% elif readingProgress and availProgress and int(readingProgress) < int(availProgress):
					<td bgcolor="${colours["hasUnread"]}" class="padded">${readingProgress}</td>
				% else:
					<td  class="padded">${readingProgress}</td>
				% endif

				% if availProgress == -1 and readingProgress == -1:
					<td class="padded">Finished</td>
				% elif availProgress and int(availProgress) > 0:
					<td class="padded">${int(availProgress)}</td>
				% else:
					<td class="padded"></td>
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


<%def name="gentagTable(tags=None, genre=None)">
	<%
	if tags:
		linkFunc = makeTagLink
		iterable = tags
	elif genre:
		linkFunc = makeGenreLink
		iterable = genre
	else:
		return genTagError(errStr="No table type (tags, genre) specified in gentagTable() call!")
	%>

	<table border="1px" style="width: 100%;">
		<tr>
				<th class="uncoloured" style="width: 400px; min-width: 400px;">Tag</th>
				<th class="uncoloured" style="width: 35px; min-width: 35px;">Matches</th>
		</tr>

		% for tag, quantity in iterable:

			<tr>
				<td>
					${linkFunc(tag)}
				</td>
				<td>
					${quantity}
				</td>
			</tr>
		% endfor


	</table>
</%def>



<%def name="genOptionRow(tags=False, genres=False)">

	<%
	letters = string.digits+string.ascii_lowercase

	if tags:
		pathPrefix = "tags"
	elif genres:
		pathPrefix = "genres"
	else:
		return genTagError()

	%>
	<div>
		<div>
			<a href='/tags/${pathPrefix}'>None</a>
			% for letter in letters:
				<%
				params = request.params.copy();
				params["prefix"] = letter
				url = "/tags/" + pathPrefix + "?" + urllib.parse.urlencode(params)
				%>
				<a href='${url}'>${letter.upper()}</a>
			% endfor
		</div>
		<div>

			<%
			params = request.params.copy();
			params["sort"] = 'number'
			url = "/tags/" + pathPrefix + "?" + urllib.parse.urlencode(params)
			%>
			<a href='${url}'>Sort by tag occurances</a>
			<%
			params = request.params.copy();
			params["sort"] = 'alphabetical'
			url = "/tags/" + pathPrefix + "?" + urllib.parse.urlencode(params)
			%>
			<a href='${url}'>Sort Alphabetically</a>
		</div>
	</div>
</%def>


<%def name="genTagBody(tag=None, genre=None)">
	<%
	if not tag and not genre:
		print("WAT?")
		return genTagError()
	%>
	<div>
		${sideBar.getSideBar(sqlCon)}
		<div class="maindiv">

			<div class="subdiv skId">
				<div class="contentdiv">
					% if tag:
						<h3>Manga Tag: ${tag}</h3>

						${genOptionRow(tags=True)}
						<div id='mangatable'>
							${genTableForTag(tag=tag)}
						</div>
					% elif genre:
						<h3>Manga Genre: ${genre}</h3>

						${genOptionRow(genres=True)}
						<div id='mangatable'>
							${genTableForTag(tag=tag, genre=genre)}
						</div>
					% else:
						<%
						raise ValueError("WAT?")
						%>
					% endif

				</div>
			</div>

		</div>
	</div>


</%def>


<%def name="genTagError(errStr=None)">

	<div class="errorPattern">
		<h3>Error</h3>
		% if not errStr:
			<p>No tag specified!</p>
		% else:
			<p>${errStr}</p>

		% endif
	</div>


</%def>
