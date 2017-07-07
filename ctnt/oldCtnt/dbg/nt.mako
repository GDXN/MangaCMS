## -*- coding: utf-8 -*-
<!DOCTYPE html>



<%
startTime = time.time()
# print("Rendering begun")
%>


<%!
import time
import settings
import os
import nameTools as nt

%>
<%namespace name="tableGenerators" file="/gentable.mako"/>
<%namespace name="sideBar"         file="/gensidebar.mako"/>
<%namespace name="ut"              file="/utilities.mako"/>
<%namespace name="ap"              file="/activePlugins.mako"/>


<%def name="genNtInternalsTable()">
	<%

	%>

	<ul>
		% for key, contDict in nt.dirNameProxy.getDirDicts().items():
			<li>
				${key}
				<table>
					<tr>
						<th>Key</th>
						<th>Value</th>
					</tr>
					% for subkey, value in contDict.items():

						<tr>
							<td>${subkey}</td>
							<td>${value}</td>
						</tr>
					% endfor


					## % for key, item in nt.dirNameProxy.iteritems():
					## 	<tr>
					## 		<td>${key}</td>
					## 		<td>${item.pop('sourceDict', None)}</td>
					## 		<td>${item}</td>
					## 	</tr>
					## % endfor
				</table>
			</li>
		% endfor
	</ul>

</%def>

<html>
	<head>
		<title>WAT WAT IN THE BATT</title>

		${ut.headerBase()}


	</head>







	<body>
		<div>
			${sideBar.getSideBar(sqlCon)}
			<div class="maindiv">

				<div class="subdiv skId">
					<div class="contentdiv">
						<h3>Nametools Internal Values</h3>
						<div id='mangatable'>
							${genNtInternalsTable()}
						</div>
					</div>
				</div>


			</div>
		</div>


		<%
		fsInfo = os.statvfs(settings.mangaFolders[1]["dir"])
		stopTime = time.time()
		timeDelta = stopTime - startTime
		%>

		<p>
			This page rendered in ${timeDelta} seconds.<br>
			Disk = ${int((fsInfo.f_bsize*fsInfo.f_bavail) / (1024*1024))/1000.0} GB of  ${int((fsInfo.f_bsize*fsInfo.f_blocks) / (1024*1024))/1000.0} GB Free.
		</p>

	</body>
</html>