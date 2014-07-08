## -*- coding: utf-8 -*-
<!DOCTYPE html>
<%startTime = time.time()%>

<%namespace name="tableGenerators" file="/gentable.mako"/>
<%namespace name="sideBar" file="/gensidebar.mako"/>
<%namespace name="reader" file="/reader/readBase.mako"/>


<%!
# Module level!
import time
import datetime
from babel.dates import format_timedelta
import os.path
import os


from operator import itemgetter

import nameTools as nt
import unicodedata
import traceback
import settings
import urllib.parse

styles = ["mtMainId", "mtSubId", "djMoeId", "fuFuId"]

def dequoteDict(inDict):
	ret = {}
	for key in inDict.keys():
		ret[key] = urllib.parse.unquote_plus(inDict[key])
	return ret

%>



<%


%>
