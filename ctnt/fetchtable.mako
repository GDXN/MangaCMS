## -*- coding: utf-8 -*-


<%namespace name="tableGenerators" file="gentable.mako"/>

<%namespace name="ap"              file="activePlugins.mako"/>

<%def name="getMangaTable()">

	${tableGenerators.genLegendTable()}
	${tableGenerators.genMangaTable(tableKey=ap.attr.inHomepageMangaTable, distinct=True, limit=200)}

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
