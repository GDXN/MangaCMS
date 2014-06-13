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
import magic

from operator import itemgetter

import nameTools as nt
import unicodedata
import traceback
import settings
import urllib.parse

import zipfile
import rarfile

styles = ["mtMainId", "mtSubId", "djMoeId", "fuFuId"]

def dequoteDict(inDict):
	ret = {}
	for key in inDict.keys():
		ret[key] = urllib.parse.unquote_plus(inDict[key])
	return ret

%>


<%

try:
	sourceSite = request.matchdict['source']
	itemId = int(request.matchdict['mId'])
except ValueError:
	reader.invalidKey()

siteTableMap = {
	"djm"    : "DoujinMoeItems",
	"fufufuu": "FufufuuItems"
}

if not sourceSite in siteTableMap:
	reader.invalidKey()
	return


cur = sqlCon.cursor()
ret = cur.execute('''SELECT downloadPath, fileName FROM %s WHERE rowid=?''' % siteTableMap[sourceSite], (itemId, ))

rets = ret.fetchall()[0]
if not rets:
	reader.invalidKey()
	return
itemPath = os.path.join(*rets)
print("dlPath = ", itemPath)


if not (os.path.isfile(itemPath) and os.access(itemPath, os.R_OK)):
	reader.invalidKey()
	return

try:
	# We have a valid file-path. Read it!
	sessionArchTool.checkOpenArchive(itemPath)

	keys = list(sessionArchTool.items.keys())
	keys.sort()

	keyUrls = []
	for key in keys:
		keyUrls.append("'/pron/%s/%s/%s'" % (urllib.parse.quote(request.matchdict['source']),
												urllib.parse.quote(request.matchdict['mId']),
												key))

	reader.showMangaItems(itemPath, keyUrls)

except:
	reader.badFileError(itemPath)


%>

