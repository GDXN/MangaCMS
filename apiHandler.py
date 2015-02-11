

import traceback
from pyramid.response import Response

import DbManagement.MonitorTool
import nameTools as nt
import logging
import json
import settings
import urllib.parse
import os.path
import os
import shutil

class ApiInterface(object):

	log = logging.getLogger("Main.API")

	def __init__(self, sqlInterface):
		self.conn = sqlInterface


	def updateSeries(self, request):

		inserter = DbManagement.MonitorTool.Inserter()

		ret = ""
		# Sooooo hacky. Using **{dict} crap in ALL THE PLACES

		self.log.info("Parameter update call!")

		if "old_buName" in request.params and "new_buName" in request.params or \
			"old_mtName" in request.params and "new_mtName" in request.params or \
			"old_buId" in request.params and "new_buId" in request.params or \
			"old_mtId" in request.params and "new_mtId" in request.params:

			if "old_buName" in request.params:
				key = "buName"
			elif "old_mtName" in request.params:
				key = "mtName"
			elif "old_mtId" in request.params:
				key = "mtId"
			elif "old_buId" in request.params:
				key = "buId"

			else:
				raise ValueError("WAT")

			self.log.info("Updating {colName} Column".format(colName=key))

			newName = request.params["new_{colName}".format(colName=key)].rstrip().lstrip()
			oldName = request.params["old_{colName}".format(colName=key)].rstrip().lstrip()
			updRowId = int(request.params["id"].rstrip().lstrip())

			existingRow = {key: newName}
			existingRow = inserter.getRowByValue(**existingRow)
			mergeRow    = inserter.getRowByValue(dbId=updRowId)

			self.log.info("mergeRow= %s", mergeRow)
			self.log.info("existingRow= %s", existingRow)

			if key == "mtId" or key == "buId":

				try:
					int(newName)
				except ValueError:
					traceback.print_exc()
					self.log.info("Values = '%s'", newName)
					ret = json.dumps({"Status": "Failed", "Message": "IDs is not anm integer!"})
					return Response(body=ret)

			updateDat = {key: newName}
			if not existingRow:
				inserter.updateDbEntry(mergeRow['dbId'], **updateDat)
				ret = json.dumps({"Status": "Succeeded", "Message": "Updated Row!"})
			else:
				fromDict = {"dbId": updRowId}
				toDict = {"dbId": existingRow['dbId']}
				inserter.mergeItems(fromDict, toDict)
				ret = json.dumps({"Status": "Succeeded", "Message": "Merged Rows!"})
		else:
			ret = json.dumps({"Status": "Failed", "Message": "Invalid argument!"})

		return Response(body=ret)


	def changeRating(self, request):
		self.log.info(request.params)

		if not "new-rating" in request.params:
			return Response(body=json.dumps({"Status": "Failed", "Message": "No new rating specified in rating-change call!"}))

		mangaName = request.params["change-rating"]
		newRating = request.params["new-rating"]

		try:
			newRating = float(newRating)
		except ValueError:
			return Response(body=json.dumps({"Status": "Failed", "Message": "New rating was not a number!"}))

		if not mangaName in nt.dirNameProxy:
			return Response(body=json.dumps({"Status": "Failed", "Message": "Specified Manga Name not in dir-dict."}))

		self.log.info("Calling ratingChange")
		nt.dirNameProxy.changeRating(mangaName, newRating)
		self.log.info("ratingChange Complete")

		return Response(body=json.dumps({"Status": "Success", "Message": "Directory Renamed"}))

	def resetDownload(self, request):
		self.log.info(request.params)

		dbId = request.params["reset-download"]

		try:
			dbId = int(dbId)
		except ValueError:
			return Response(body=json.dumps({"Status": "Failed", "Message": "Row ID was not a integer!"}))

		cur = self.conn.cursor()

		cur.execute("SELECT dlState, dbid FROM MangaItems WHERE dbId=%s", (dbId, ))
		ret = cur.fetchall()

		if len(ret) == 0:
			return Response(body=json.dumps({"Status": "Failed", "Message": "Row ID was not present in DB!"}))
		if len(ret) != 1:
			return Response(body=json.dumps({"Status": "Failed", "Message": "Did not receive single row for query based on RowId"}))

		dlState, qId = ret[0]

		if qId != dbId:
			return Response(body=json.dumps({"Status": "Failed", "Message": "Id Mismatch! Wat?"}))

		if dlState >= 0:
			return Response(body=json.dumps({"Status": "Failed", "Message": "Row does not need to be reset!"}))


		cur.execute("UPDATE MangaItems SET dlState=0 WHERE dbId=%s", (dbId, ))
		cur.execute("COMMIT;")

		return Response(body=json.dumps({"Status": "Success", "Message": "Download state reset."}))


	def getHentaiTrigramSearch(self, request):

		itemNameStr = request.params['trigram-query-hentai-str']
		linkText = request.params['trigram-query-linktext']

		cur = self.conn.cursor()
		cur.execute("""SELECT COUNT(*) FROM hentaiitems WHERE originname %% %s;""", (itemNameStr, ))
		ret = cur.fetchone()[0]

		if ret:
			ret = "<a href='/search-h/h?q=%s'>%s</a>" % (urllib.parse.quote_plus(itemNameStr.encode("utf-8")), linkText)
		else:
			ret = 'No H Items'

		return Response(body=json.dumps({"Status": "Success", "contents": ret}))



	def getBookTrigramSearch(self, request):

		itemNameStr = request.params['trigram-query-book-str']
		linkText = request.params['trigram-query-linktext']

		cur = self.conn.cursor()
		cur.execute("""SELECT COUNT(*) FROM book_items WHERE title %% %s;""", (itemNameStr, ))
		ret = cur.fetchone()[0]

		if ret:
			ret = "<a href='/search-b/b?q=%s'>%s</a>" % (urllib.parse.quote_plus(itemNameStr.encode("utf-8")), linkText)
		else:
			ret = 'No Book Items'

		return Response(body=json.dumps({"Status": "Success", "contents": ret}))


	def deleteItem(self, request):

		srcDict = request.params['src-dict']
		srcText = request.params['src-path']

		srcPathBase = settings.mangaFolders[int(srcDict)]['dir']
		srcPathFrag = urllib.parse.unquote(srcText)
		print(srcPathBase)
		print(srcPathFrag)
		fqPath = os.path.join(srcPathBase, srcPathFrag)

		if not os.path.exists(fqPath):
			return Response(body=json.dumps({"Status": "Failed", "contents": "Item does not exist?"}))

		if not os.path.exists(settings.recycleBin):
			os.mkdir(settings.recycleBin)


		dst = fqPath.replace("/", ";")
		dst = os.path.join(settings.recycleBin, dst)
		self.log.info("Moving item from '%s'", fqPath)
		self.log.info("              to '%s'", dst)
		try:
			shutil.move(fqPath, dst)
			# self.addTag(fqPath, "manually-deleted")

		except OSError:
			self.log.error("ERROR - Could not move file!")
			self.log.error(traceback.format_exc())
			return Response(body=json.dumps({"Status": "Failed", "contents": 'Could not move file?'}))


		return Response(body=json.dumps({"Status": "Success", "contents": 'Item moved to recycle bin!'}))


	def handleApiCall(self, request):

		self.log.info("API Call! %s", request.params)

		if request.remote_addr in settings.noHighlightAddresses:
			return Response(body=json.dumps({"Status": "Failed", "Message": "API calls are blocked from the reverse-proxy IP."}))


		if "change-rating" in request.params:
			self.log.info("Rating change!")
			return self.changeRating(request)
		elif "update-series" in request.params:
			self.log.info("Update series!")
			return self.updateSeries(request)
		elif "reset-download" in request.params:
			self.log.info("Download Reset!")
			return self.resetDownload(request)
		elif "trigram-query-hentai-str" in request.params and "trigram-query-linktext" in request.params:
			self.log.info("Trigram query existence check")
			return self.getHentaiTrigramSearch(request)
		elif "trigram-query-book-str" in request.params and "trigram-query-linktext" in request.params:
			self.log.info("Trigram query existence check")
			return self.getBookTrigramSearch(request)
		elif 'delete-item' in request.params:
			return self.deleteItem(request)

		else:
			self.log.warning("Unknown API call")
			self.log.warning("Call params: '%s'", request.params)
			return Response(body="wat?")
