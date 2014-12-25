## -*- coding: utf-8 -*-


<%namespace name="tableGenerators" file="gentable.mako"/>

<%namespace name="ap"              file="activePlugins.mako"/>


<%def name="getMangaTable(tableKey=None, distinct=True, limit=200, boldNew=True, offset=0)">
	<%
	# You can't have 'ap.attr.inHomepageMangaTable' as the default value in a mako function, apparently
	if tableKey == None:
		tableKey = ap.attr.inHomepageMangaTable
	%>
	${tableGenerators.genLegendTable()}
	${tableGenerators.genMangaTable(tableKey=tableKey, distinct=distinct, limit=limit, offset=offset, boldNew=boldNew)}

</%def>


<%def name="getPronTable()">

	${tableGenerators.genLegendTable(pron=True)}
	${tableGenerators.genPronTable()}

</%def>


<%def name="error()">

	LOLWAT?

</%def>





<%

# If there is no items in the request path, display the root dir
if not "table" in request.params:
	error()
	return

if   request.params["table"] == "manga":
	getMangaTable()
elif request.params["table"] == "pron":
	getPronTable()
else:
	error()


%>
