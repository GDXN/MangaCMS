## -*- coding: utf-8 -*-
<!DOCTYPE html>
<%!
# Module level!

import time
import datetime
from babel.dates import format_timedelta

import statusManager as sm
import nameTools as nt


%>

<%def name="get_all_books()">

	<%

	cur = sqlCon.cursor()
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


