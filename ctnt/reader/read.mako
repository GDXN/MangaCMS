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

item = request.matchdict['seriesName']
dictKey = int(request.matchdict['dict'])

if not dictKey in settings.mangaFolders:
	reader.invalidKey()
	return
# if not item in nt.dirNameProxy:
# 	reader.invalidKey()
# 	return
dirPath = nt.dirNameProxy.getFromSpecificDict(dictKey, item)["fqPath"]
if dirPath == None:
	return

# HACK - Work around cherryPy encoding being TOTALLY FUCKED
request.matchdict["fileName"] = request.matchdict["fileName"].encode('latin1').decode('utf-8')

itemPath = os.path.join(dirPath, request.matchdict["fileName"])
# print("Dirpath = ", itemPath)

if not (os.path.isfile(itemPath) and os.access(itemPath, os.R_OK)):
	print("")
	reader.invalidKey()
	return



try:
	# We have a valid file-path. Read it!
	sessionArchTool.checkOpenArchive(itemPath)
	print("sessionArchTool", sessionArchTool)
	keys = sessionArchTool.getKeys()  # Keys are already sorted

	print("Items in archive", keys)
	print("Items in archive", sessionArchTool.items)

	keyUrls = []
	for key in keys:
		keyUrls.append("'/reader/%s/%s/%s/%s'" % (urllib.parse.quote(request.matchdict['dict']),
												urllib.parse.quote(request.matchdict['seriesName']),
												urllib.parse.quote(request.matchdict['fileName']),
												key))

	reader.showMangaItems(itemPath, keyUrls)
except:
	print("Bad file")
	reader.badFileError(itemPath)



%>
