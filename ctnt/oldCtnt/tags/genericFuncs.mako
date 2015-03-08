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
	cur.execute("SELECT buName, buId, readingProgress, availProgress, butags, bugenre FROM mangaseries WHERE %s::tsquery @@ lower(butags)::tsvector ORDER BY buName ASC;", (tag.lower(), ))
	rows = cur.fetchall()
	return rows
	%>
</%def>
<%def name="getSeriesForGenre(genre)">
	<%
	cur = sqlCon.cursor()
	cur.execute("SELECT buName, buId, readingProgress, availProgress, butags, bugenre FROM mangaseries WHERE %s::tsquery @@ lower(buGenre)::tsvector ORDER BY buName ASC;", (genre.lower(), ))
	rows = cur.fetchall()
	return rows
	%>
</%def>

<%def name="genTableForTag(tag=None, genre=None, exists='all')">
	<%

	if tag:
		rows = getSeriesForTag(tag)
	elif genre:
		rows = getSeriesForGenre(genre)
	else:
		print(tag, genre)
		return genTagError(errStr="No tag specified to table generator!")

	keys = [
		'seriesName',
		'muId',
		'readChapter',
		'currentChapter',
		'tags',
		'genre',
	]

	processed = []
	for row in rows:
		item = dict(zip(keys, row))
		# print(item)
		item['itemInfo'] = nt.dirNameProxy[item["seriesName"]]


		# If an item has a non-none fqPath, and exists is 'no', skip it so it's not
		# displayed.
		# Also, if an item has a none fqPqth, it /doesn't/ exist. If exists == yes, skip it.
		if exists == 'yes' and item['itemInfo']['fqPath'] == None:
			continue
		elif exists == 'no' and item['itemInfo']['fqPath'] != None:
			continue



		processed.append(item)

	tableGenerators.genSeriesListingTable(processed)

	%>
</%def>






<%def name="makeTagLink(tag, params='')">
	<a href='/tags/tag?tag=${tag | u}${params}'>${tag}</a>
</%def>


<%def name="makeGenreLink(genre, params='')">
	<a href='/tags/genre?genre=${genre | u}${params}'>${genre}</a>
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



<%def name="genAZdiv(pathPrefix, request)">
	<%

	letters = string.digits+string.ascii_lowercase
	%>
	<div style='float:left'>
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
</%def>




<%def name="genExistenceFilterdiv(pathPrefix, request)">
	<%
	options = [('All', 'all'), ('Dir Found', 'yes'), ('No Dir', 'no')]
	%>
	<div style='float:left'>
		% for name, option in options:
			<%
			params = request.params.copy();
			params["showonlyexists"] = option
			url = "/tags/" + pathPrefix + "?" + urllib.parse.urlencode(params)
			%>
			<a href='${url}'>${name}</a>
		% endfor
	</div>
</%def>




<%def name="genSortOrderDiv(pathPrefix, request)">
	<%

	letters = string.digits+string.ascii_lowercase
	%>
	<div style='float:right'>

		<%
		params = request.params.copy();
		params["sort"] = 'number'
		url = "/tags/" + pathPrefix + "?" + urllib.parse.urlencode(params)
		%>
		<a href='${url}'>Sort by ${pathPrefix.strip("s")} occurances</a>,
		<%
		params = request.params.copy();
		params["sort"] = 'alphabetical'
		url = "/tags/" + pathPrefix + "?" + urllib.parse.urlencode(params)
		%>
		<a href='${url}'>Sort Alphabetically</a>
	</div>
</%def>



<%def name="genOptionRow(tags=False, genres=False)">

	<%

	if tags:
		pathPrefix = "tags"
	elif genres:
		pathPrefix = "genres"
	else:
		return genTagError()

	%>
	<div>
		${genAZdiv(pathPrefix, request)}
		${genSortOrderDiv(pathPrefix, request)}

	</div>
</%def>


<%def name="genItemDisplayOptionRow(tags=False, genres=False)">

	<%

	if tags:
		pathPrefix = "tag"
	elif genres:
		pathPrefix = "genre"
	else:
		return genTagError()

	%>
	<div style='display:inline-block; width:100%'>
		${genExistenceFilterdiv(pathPrefix, request)}
		${genSortOrderDiv(pathPrefix, request)}

	</div>
</%def>


<%def name="genTagBody(tag=None, genre=None)">
	<%
	if not tag and not genre:
		print("WAT?")
		return genTagError()



	validExistsValues = ['yes', 'no', 'all']

	exists = 'yes'
	if 'showonlyexists' in request.params:
		if request.params['showonlyexists'] in validExistsValues:
			exists = request.params['showonlyexists']

		else:
			genTagError()
			return


	%>
	<div>
		${sideBar.getSideBar(sqlCon)}
		<div class="maindiv">

			<div class="subdiv skId">
				<div class="contentdiv">
					% if tag:
						<h3>Manga Tag: ${tag}</h3>

						${genItemDisplayOptionRow(tags=True)}
						<div id='mangatable'>
							${genTableForTag(tag=tag, exists=exists)}
						</div>
					% elif genre:
						<h3>Manga Genre: ${genre}</h3>

						${genItemDisplayOptionRow(genres=True)}
						<div id='mangatable'>
							${genTableForTag(tag=tag, genre=genre, exists=exists)}
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
