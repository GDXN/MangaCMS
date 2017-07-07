## base.html
<!DOCTYPE html>
<%!
import time
import settings
import os
%>

<%
startTime = time.time()
%>


<%namespace name="utilities" file="/model/utilities.mako"/>

<%namespace name="sidebar"   file="/view/sidebar.mako"/>



<html>
	<head>
		<%block name="head">

			${utilities.headerBase()}
			<script>

				function searchMUForItem(formId)
				{

					var form=document.getElementById(formId);
					form.submit();
				}

				${utilities.mouseOverJs('showTT')}
			</script>

			<script type="text/javascript" src="/js/jquery-2.1.0.min.js"></script>
			<script type="text/javascript" src="/js/jquery.waypoints.js"></script>
			<meta name="viewport" content="width=1024" />

			<title><%block name="title">No Title!</%block></title>

			<%block name="extra_scripts">
				## Nothing in the base
			</%block>
		</%block>

	</head>

	<body>
		<div>

			${sidebar.getSideBar(sqlCon)}

			<div class="maindiv">
				<%block name="body_content">
					Empty Body!
				</%block>
			</div>

		</div>

		<%
		fsInfo = os.statvfs(settings.mangaFolders[1]["dir"])
		stopTime = time.time()
		timeDelta = stopTime - startTime
		%>
		<p>
			This page rendered in ${timeDelta} seconds.<br>
			Disk = ${int((fsInfo.f_bsize*fsInfo.f_bavail) / (1024*1024*1024))/1000.0} TB of  ${int((fsInfo.f_bsize*fsInfo.f_blocks) / (1024*1024*1024))/1000.0} TB Free.
		</p>

	</body>
</html>