## -*- coding: utf-8 -*-


<%!
import nameTools as nt
import unicodedata
import traceback
import settings
import os.path
import urllib
%>
<%
# print("Rendering")
%>


<%namespace name="ut"              file="/utilities.mako"/>
<%namespace name="sideBar"         file="/gensidebar.mako"/>
<%namespace name="reader" file="/reader2/readBase.mako"/>



<%
print("Matchdict", request.matchdict)

if not "mId" in request.matchdict:

	reader.invalidKey(title="No itemId in url. How did you even get here?")
	return

try:
	itemId = int(request.matchdict["mId"])
except ValueError:
	reader.invalidKey(message="Specified itemId is not a integer!")
	return

with sqlCon.cursor() as cur:
	ret = cur.execute('''SELECT downloadPath, fileName FROM HentaiItems WHERE dbId=%s;''', (itemId, ))
	rets = cur.fetchall()[0]

if not rets:
	reader.invalidKey(message="Specified itemId does not exist in database!")
	return

# print("Key", rets)
itemPath = os.path.join(*rets)
# print("dlPath = ", itemPath)

if not (os.path.isfile(itemPath) and os.access(itemPath, os.R_OK)):
	reader.invalidKey(message="File corresponding to key does not seem to exist.")
	return

reader.showMangaItems(itemPath)

%>

