
<%!
# Module level!
import time
import datetime
import os.path


import re
import urllib.parse
import nameTools as nt


%>






<%def name="timeAgo(inTimeStamp)">
	<%
	if inTimeStamp == None:
		return "NaN"
	delta = int(time.time() - inTimeStamp)
	if delta < 60:
		return "{delta} s".format(delta=delta)
	delta = delta // 60
	if delta < 60:
		return "{delta} m".format(delta=delta)
	delta = delta // 60
	if delta < 24:
		return "{delta} h".format(delta=delta)
	delta = delta // 24
	return "{delta} d".format(delta=delta)

	%>
</%def>



<%def name="idToLink(buId=None, mtId=None)">
	<%

	if mtId:
		return "<a href='http://www.mangatraders.com/manga/series/{id}'>{id}</a>".format(id=mtId)
	elif buId:
		return "<a href='http://www.mangaupdates.com/series.html?id={id}'>{id}</a>".format(id=buId)
	else:
		return ""

	%>
</%def>



<%def name="createReaderLink(itemName, itemInfo)">
	<%

	if itemInfo == None or itemInfo["item"] == None:
		if itemName:
			return itemName
		else:
			return ""

	return "<a href='/reader/%s/%s'>%s</a>" % (itemInfo["sourceDict"], urllib.parse.quote(itemInfo["dirKey"]), itemName)

	%>
</%def>


<%def name="headerBase()">
	<link rel="stylesheet" href="/style.css">
	<script type="text/javascript" src="/js/jquery-2.1.0.min.js"></script>
	<script>

		function searchMUForItem(formId)
		{

			var form=document.getElementById(formId);
			form.submit();
		}

	</script>
</%def>


<%def name="nameToBuSearch(seriesName, linkText='Manga Updates')">
	<%
		# Add hash to the function name to allow multiple functions on the same page to coexist.
		# Will probably collide if multiple instances of the same link target exist, but at that point, who cares? They're the same link target, so
		# therefore, the same search anyways.

		itemHash = abs(hash(seriesName))

		buLink = '<a href="javascript: searchMUForItem_%d()">%s</a>' % (itemHash, linkText)
		buLink += '<script>function searchMUForItem_%d(){ var form=document.getElementById("muSearchForm"); form.submit(); }</script>' % itemHash
		return buLink
	%>
</%def>

<%def name="nameToMtSearch(seriesName, linkText='Manga Traders')">
	<%
		link = '<a href="http://www.mangatraders.com/search/?term=%s&Submit=Submit&searchSeries=1">%s</a>' % (urllib.parse.quote(seriesName), linkText)
		return link
	%>
</%def>


<%def name="getItemInfo(seriesName)">
	<%
	cur = sqlCon.cursor()
	ret = cur.execute("SELECT buId,buTags,buGenre,buList FROM MangaSeries WHERE buName=?;", (seriesName, ))
	rets = ret.fetchall()
	if not rets:
		buId, buTags, buGenre, buList = None, None, None, None
	else:
		buId, buTags, buGenre, buList = rets[0]
	print("Looked up item %s, ret=%s" % (seriesName, buId))

	if buId:
		haveBu = True
		buLink = '<a href="http://www.mangaupdates.com/series.html?id=%s">Manga Updates</a>' % buId
	else:
		haveBu = False
		buLink = nameToBuSearch(seriesName)

	return (haveBu, buLink, buTags, buGenre, buList)
	%>
</%def>

