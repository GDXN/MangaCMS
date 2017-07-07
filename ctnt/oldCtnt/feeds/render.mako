## -*- coding: utf-8 -*-
<!DOCTYPE html>
<%!
import time
import urllib.parse
%>

<%namespace name="sideBar"         file="/gensidebar.mako"/>
<%namespace name="ut"              file="/utilities.mako"/>

<%def name="getBaseDomainUrl(url)">
	<%
	parsedUrl = urllib.parse.urlsplit(url)
	feedurl = parsedUrl.netloc
	itemHome = '/books/?loc='+parsedUrl.netloc
	#tup = (parsedUrl.scheme, parsedUrl.netloc, '', '', '')
	#itemHome = urllib.parse.urlunsplit(tup)




	return feedurl, itemHome
	%>

</%def>


<%def name="fetchEntries(offset, quantity)">
	<%

	cur = sqlCon.cursor()
	cur.execute('''SELECT
				dbid,
				srcname,
				feedurl,
				contenturl,
				contentid,
				title,
				author,
				tags,
				updated,
				published
			FROM
				rss_monitor
			WHERE
				srcname != 'tsuki' AND
				srcname != 'remonwiki'
			ORDER BY published desc
			LIMIT %s
			OFFSET %s''', (quantity, offset))

	## Baka-Tsuki's RSS feed is too full of crap
	## to be worth rendering (though it's still nice for
	## change monitoring)

	ret = cur.fetchall()

	keys = [
				'dbid',
				'srcname',
				'feedurl',
				'contenturl',
				'contentid',
				'title',
				'author',
				'tags',
				'updated',
				'published',
			]
	data = [dict(zip(keys, item)) for item in ret]


	return data

	%>
</%def>


<%def name="renderRow(rowDat)">
	<%
	title = rowDat['title']
	feedurl, itemHome = getBaseDomainUrl(rowDat['feedurl'])

	source = rowDat['srcname'].title()
	date = ut.timeAgo(rowDat['published'])
	tags = rowDat['tags']
	tags = ", ".join(tags)

	%>
	<tr>
		<td><a href='/feeds/item?entry=${rowDat['dbid']}'>${title}</a></td>
		<td><a href='${itemHome}'>${feedurl}</a><span style='float:right'><a href='${rowDat['contenturl']}'>src</a></span></td>
		<td>${tags}</td>
		<td>${date}</td>
	</tr>
</%def>

<%def name="renderTable(data)">
	<table border="1px" style="width: 100%;">
		<tr>
			<th style="width: 400px; min-width: 400px;"  class="uncoloured">Title</th>
			<th style="width: 200px; min-width: 200px;"  class="uncoloured">Source</th>
			<th  class="uncoloured">Tags</th>
			<th style="width: 60px; min-width: 60px;"  class="uncoloured">Date</th>
		</tr>
		%for entry in data:
			<%
			renderRow(entry)
			%>
		%endfor
	</table>
</%def>

<%def name="renderRss(offset=0, quantity=200)">
	Rss render call!

	<%

	dat = fetchEntries(offset, quantity)
	renderTable(dat)

	%>

</%def>


<%def name="itemId(itemId)">
	<%
	cur = sqlCon.cursor()
	cur.execute('''SELECT
				dbid,
				srcname,
				feedurl,
				contenturl,
				contentid,
				title,
				contents,
				author,
				tags,
				updated,
				published
			FROM
				rss_monitor
			WHERE
				dbid= %s''', (itemId, ))
	data = cur.fetchone()


	keys = ['dbid', 'srcname', 'feedurl', 'contenturl', 'contentid', 'title', 'contents', 'author', 'tags', 'updated', 'published']

	data = dict(zip(keys, data))


	itemHomeName, baseUrl = getBaseDomainUrl(data['contenturl'])


	%>
	<hr>
	<h2>
		${data['title']}
	</h2>

	<div>
		<table>

			<col width="200px">
			<col width="400px">
			<tr>
				<td>
					Title:
				</td>
				<td>
					<%
					ut.createBookTitleSearch(data['title'], data['title'])
					%>
				</td>
			</tr>
			<tr>
				<td>
					Source:
				</td>
				<td>
					<a href='${baseUrl}'>${itemHomeName}</a>
				</td>
			</tr>

			<tr>
				<td>
					Tags:
				</td>
				<td>
					${', '.join(data['tags'])}
				</td>
			</tr>
			<tr>
				<td>
					Author:
				</td>
				<td>
					${data['author'] if data['author'] else 'Not Present!'}
				</td>
			</tr>

			<tr>
				<td>
					Full Local Content:
				</td>
				<td>
					<%
						ut.makeBookReaderLinkFromUrl(data['contenturl'], data['title'])
					%>
				</td>
			</tr>

		</table>
	</div>
	<div class='subdiv' style='padding:5px'>

		<script type="text/javascript">

			function asyncRequest(targetUrl, replaceId)
			{
				$.get(targetUrl,
					function( response, status, xhr )
					{
						if ( status == "error" )
						{
							var msg = "Sorry but there was an error: ";
							$( "#error" ).html( msg + xhr.status + " " + xhr.statusText );
						}
						else
						{
							console.log('Output: ', replaceId)
							$('#'+replaceId).html(response);
						}
					}
				);
			};

		</script>
		<%
		searches = [data['title']]
		for tag in data['tags']:
			searches.append(tag)
		%>
		% for entry in searches:

			<div id='delLoad-${id(entry)}'>
				<strong>Search results for item</strong> '${entry}':
				<script>

					$(document).ready(function() {
						asyncRequest('/books/renderSearch?searchSeries=${entry|u}', 'delLoad-${id(entry)}');

					});

				</script>
				<center><img src='/js/loading.gif' /></center>
			</div>
		%endfor

	</div>


	<div class='bookdiv'>
		<div class="contentdiv bookcontent">

			${data['contents']}
		</div>
	</div>


	## <%

	## dat = fetchEntries(offset, quantity)
	## renderTable(dat)

	## %>

</%def>


