## -*- coding: utf-8 -*-
<!DOCTYPE html>
<%!
# Module level!

import time
import datetime
from babel.dates import format_timedelta

import statusManager as sm
import nameTools as nt

FAILED = -1
QUEUED = 0
DLING  = 1
DNLDED = 2

%>
<%namespace name="utilities" file="/model/utilities.mako"/>
<%namespace name="ap" file="/model/activePlugins.mako"/>


<%def name="fetchSidebarCounts(sqlConnection)">

	<%

	cur = sqlConnection.cursor()
	cur.execute("ROLLBACK;")

	# Counting crap is now driven by commit/update/delete hooks
	ret = cur.execute('SELECT sourceSite, dlState, quantity FROM MangaItemCounts;')
	rets = cur.fetchall()

	statusDict = {}
	for srcId, state, num in rets:
		if not srcId in statusDict:
			statusDict[srcId] = {}
		if not state in statusDict[srcId]:
			statusDict[srcId][state] = num
		else:
			statusDict[srcId][state] += num



	return statusDict
	%>
</%def>



<%def name="fetchSidebarPluginStatus(sqlConnection)">

	<%

	cur = sqlConnection.cursor()
	cur.execute("ROLLBACK;")


	retNormal = []
	retAdult  = []
	for item in ap.attr.sidebarItemList:


		if not item["renderSideBar"]:
			continue
		if not item["dbKey"]:
			continue

		vals = sm.getStatus(cur, item["dbKey"])
		if vals:
			item['running'], item['runStart'], item['lastRunDuration'], item['lastErr'] = vals[0]
			item['runStart'] = utilities.timeAgo(item['runStart'])
		else:
			item['running'], item['runStart'], item['lastRunDuration'], item['lastErr'] = False, "Never!", None, time.time()

		if item['running']:
			item['runState'] = "<b>Running</b>"
		else:
			item['runState'] = "Not Running"

		item['errored'] = False
		if item['lastErr'] > (time.time() - 60*60*24): # If the last error was within the last 24 hours
			item['errored'] = True



		if item['type'] == "Porn":
			retAdult.append(item)
		else:
			retNormal.append(item)



	if not utilities.ip_in_whitelist():
		return retNormal, []
	else:
		return retNormal, retAdult


	%>
</%def>





<%def name="fetchRandomLink()">
	<%

	try:
		randomLink = utilities.createReaderLink("Random", nt.dirNameProxy.random())
	except ValueError:
		randomLink = "Not Available"

	return randomLink
	%>
</%def>
