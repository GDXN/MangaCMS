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

validTables = [
	'mangaitems',
	'hentaiitems',
	'book_items',
	'book_western_items'
	]

%>


<%namespace name="tableGenerators" file="/gentable.mako"/>
<%namespace name="bookSearch"      file="/books/renderSearch.mako"/>
<%namespace name="sideBar"         file="/gensidebar.mako"/>
<%namespace name="ut"              file="/utilities.mako"/>
<%namespace name="ap"              file="/activePlugins.mako"/>




<%def name="genHentaiSearch(search)">
	${search}

	${tableGenerators.genPronTable(originTrigram=search)}

</%def>
<%def name="genBookSearch(search)">
	${search}
	${bookSearch.genBookSearch(originTrigram=search)}

</%def>
<%def name="genBookWesternSearch(search)">
	${search}
	${bookSearch.genBookWesternSearch(originTrigram=search)}

</%def>

<%def name="genSearchBody(search, tablename)">
	<%
	if not tablename in validTables:
		print("WAT?")
		return genSearchError("Invalid table to search!")

	%>
	<div>
		${sideBar.getSideBar(sqlCon)}
		<div class="maindiv">

			<div class="subdiv skId">
				<div class="contentdiv">
					<h3>Search for '${search}' in table ${tablename}</h3>

					<div id='mangatable'>
						% if tablename == 'hentaiitems':
							${genHentaiSearch(search)}
						% elif tablename == 'book_items':
							${genBookSearch(search)}
						% elif tablename == 'book_western_items':
							${genBookWesternSearch(search)}
						% elif tablename == 'mangaitems':
							Manga search not currently functional!
						% else:
							Wat?
						% endif

					</div>

				</div>
			</div>

		</div>
	</div>


</%def>


<%def name="genSearchError(errStr=None)">


	<div>
		${sideBar.getSideBar(sqlCon)}
		<div class="maindiv">

			<div class="subdiv skId">

					<div class="errorPattern">
						<h3>Error</h3>
						<p>${errStr}</p>

					</div>

			</div>

		</div>
	</div>



</%def>
