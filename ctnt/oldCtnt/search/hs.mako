
<%namespace name="tableGenerators" file="/gentable.mako"/>

<%

if 'q' in request.params:
	searchterm = request.params['q']
	tableGenerators.genPronTable(originTrigram=searchterm)
else:
	return("No search query specified!")

%>


