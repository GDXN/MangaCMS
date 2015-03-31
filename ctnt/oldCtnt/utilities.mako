
<%!
# Module level!
import time
import datetime
import os.path
import calendar

import re
import urllib.parse
import nameTools as nt

import settings
from ipaddress import IPv4Address, IPv4Network


%>

<%def name="ip_in_whitelist()">
	<%
		user_ip = IPv4Address(request.remote_addr)

		w_ip = IPv4Network(settings.pronWhiteList)
		if user_ip in w_ip:
			return True
		return False
	%>
</%def>

<%def name="fSizeToStr(fSize)">
	<%
	fStr = fSize/1.0e6
	if fStr < 100:
		fStr = "%0.2f M" % fStr
	else:
		fStr = "%0.1f M" % fStr

	return fStr
	%>

</%def>

<%def name="errorDiv(errStr=None)">
	<br>

	<div class="errorPattern">
		<h2>Error!</h2>
		<p>${errStr}</p>

	</div>

</%def>



<%def name="timeAgo(inTimeStamp)">
	<%
	if inTimeStamp == None:
		return "NaN"

	delta = int(time.time() - inTimeStamp)
	if delta < 0:
		return "Past?"
	elif delta < 60:
		return "{delta} s".format(delta=delta)
	delta = delta // 60
	if delta < 60:
		return "{delta} m".format(delta=delta)
	delta = delta // 60
	if delta < 24:
		return "{delta} h".format(delta=delta)
	delta = delta // 24
	if delta < 999:
		return "{delta} d".format(delta=delta)
	delta = delta // 365
	return "{delta} y".format(delta=delta)
	%>
</%def>


<%def name="timeAhead(inTimeStamp)">
	<%
	if inTimeStamp == None:
		return "NaN"

	delta = int(inTimeStamp - time.time())
	if delta < 0:
		return "Future?"
	elif delta < 60:
		return "{delta} s".format(delta=delta)
	delta = delta // 60
	if delta < 60:
		return "{delta} m".format(delta=delta)
	delta = delta // 60
	if delta < 24:
		return "{delta} h".format(delta=delta)
	delta = delta // 24
	if delta < 999:
		return "{delta} d".format(delta=delta)
	delta = delta // 365
	return "{delta} y".format(delta=delta)
	%>
</%def>

<%def name="makeBookReaderLinkFromUrl(url, linkText)">

	<a href='/books/render?url=${url | u}'>${linkText}</a>
</%def>

<%def name="makeLndbItemLink(dbid, linkText)">
	<a href='/books/book-item?lndb=${dbid | u}'>${linkText}</a>
</%def>

<%def name="makeBookItemLink(title, linkText)">
	<a href='/books/book-item?title=${title | u}'>${linkText}</a>
</%def>

<%def name="makeBookIdLink(dbid, linkText)">
	<a href='/books/book-item?dbid=${dbid | u}'>${linkText}</a>
</%def>

<%def name="makeBookListLink(listname, linkText)">
	<a href='/books/book-lists?list=${listname | u}'>${linkText}</a>
</%def>


<%def name="idToLink(buId, linktext=None)">
	<%
	if buId == False or buId == None:
		return ''
	if linktext == None:
		linktext = buId
	return "<a href='http://www.mangaupdates.com/series.html?id={id}'>{text}</a>".format(id=buId, text=linktext)

	%>
</%def>




<%def name="createReaderLink(itemName, itemInfo)">
	<%

	if itemInfo == None or itemInfo["item"] == None:
		if itemName:
			return itemName
		else:
			return ""

	return "<a href='/reader2/browse/0/%s'>%s</a>" % (urllib.parse.quote(itemInfo["dirKey"].encode("utf-8")), itemName)

	%>
</%def>




<%def name="createHentaiSearch(linkText, itemNameStr, )">
	<%
	createTrigramSearchSearch(linkText, itemNameStr, 'trigram-query-hentai-str', 'trigram-query-linktext')
	%>
</%def>
<%def name="createBookSearch(linkText, itemNameStr, )">
	<%
	createTrigramSearchSearch(linkText, itemNameStr, 'trigram-query-book-str', 'trigram-query-linktext')
	%>
</%def>

<%def name="createTrigramSearchSearch(linkText, itemNameStr, searchStr, searchText)">
	<%

	# cur = sqlCon.cursor()
	# cur.execute("""SELECT COUNT(*) FROM hentaiitems WHERE originname %% %s;""", (itemNameStr, ))
	# ret = cur.fetchone()[0]
	# if ret:

	# 	return "<a href='/search/h?q=%s'>%s</a>" % (urllib.parse.quote_plus(itemNameStr.encode("utf-8")), linkText)
	# else:
	# 	return ''

	col_id = abs(hash((linkText, itemNameStr)))




	%>
	<span id='sp${col_id}'>
		<script>

			function ajaxCallback_${col_id}(reqData, statusStr, jqXHR)
			{
				console.log("Ajax request succeeded");
				console.log(reqData);
				console.log(statusStr);

				var status = $.parseJSON(reqData);
				console.log(status)
				if (status.Status == "Success")
				{

						$('#sp${col_id}').html(status.contents);


				}
				else
				{
					$('#sp${col_id}').html("AJAX Error!");
				}

			};


			$(function() {
				$('#sp${col_id}').waypoint(
					function()
					{
						var ret = ({});
						ret["${searchStr}"] = "${itemNameStr}";
						ret["${searchText}"] = "${linkText}";
						$.ajax("/api", {"data": ret, success: ajaxCallback_${col_id}});

						// Destroy the scroll waypoint, so it doesn't trigger again.
						this.destroy();
					},
					{
						offset: '100%'
					}
					);
				});

		</script>
		<img src='/rsc/ajax-loader.gif'>
	</span>
</%def>




<%def name="getCss()">

	<link rel="stylesheet" href="/style.mako.css">
</%def>

<%def name="mouseOverJs(key='showTT')">
	// Yeah, apparently you can have raw js in
	// mako functions.

	$(document).ready(function() {
	// Tooltip only Text
	$('.${key}').hover(function(){
		// Hover over code
		var mouseovertext = $(this).attr('mouseovertext');
		$(this).data('tipText', mouseovertext).removeAttr('mouseovertext');
		$('<p class="tooltip"></p>')
		.html(mouseovertext)
		.appendTo('body')
		.fadeIn('slow');
	}, function() {
		// Hover out code
		$(this).attr('mouseovertext', $(this).data('tipText'));
		$('.tooltip').remove();
	}).mousemove(function(e) {
		var mousex = e.pageX + 20; //Get X coordinates
		var mousey = e.pageY + 10; //Get Y coordinates
		$('.tooltip')
		.css({ top: mousey, left: mousex })
	});
	});
</%def>


<%def name="headerBase(key='showTT')">
	${getCss()}
	<script type="text/javascript" src="/js/jquery-2.1.0.min.js"></script>
	<script type="text/javascript" src="/js/jquery.waypoints.js"></script>
	<script>

		function searchMUForItem(formId)
		{

			var form=document.getElementById(formId);
			form.submit();
		}

		${mouseOverJs(key)}
	</script>
	<meta name="viewport" content="width=1024" />

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
	muId = nt.getMangaUpdatesId(seriesName)

	if muId:
		with sqlCon.cursor() as cur:
			ret = cur.execute("SELECT buId,buTags,buGenre,buList,readingProgress,availProgress  FROM MangaSeries WHERE buId=%s;", (muId, ))
			rets = cur.fetchall()
		if rets:
			buId, buTags, buGenre, buList, readProgress, availProgress = rets[0]

	if not muId:
		buId, buTags, buGenre, buList, readProgress, availProgress = None, None, None, None, None, None


	if buId:
		haveBu = True
		buLink = '<a href="http://www.mangaupdates.com/series.html?id=%s">Manga Updates</a>' % buId
	else:
		haveBu = False
		buLink = nameToBuSearch(seriesName)

	return (buId, haveBu, buLink, buTags, buGenre, buList, readProgress, availProgress)
	%>
</%def>



<%def name="getUrlParam(paramName)">
	<%
	if paramName in request.params:
		return request.params[paramName]
	else:
		return None
	%>
</%def>




