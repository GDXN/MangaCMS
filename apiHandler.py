

import traceback
from pyramid.response import Response
import os.path
import DbManagement.MonitorTool
import nameTools as nt
import logging
import json
import settings

class ApiInterface(object):

	log = logging.getLogger("Main.API")

	def __init__(self, sqlInterface):
		self.conn = sqlInterface


	def updateSeries(self, request):

		inserter = DbManagement.MonitorTool.Inserter()
		ret = ""
		# Sooooo hacky. Using **{dict} crap in ALL THE PLACES

		print("Parameter update call!")

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

			print("Updating {colName} Column".format(colName=key))

			newName = request.params["new_{colName}".format(colName=key)].rstrip().lstrip()
			oldName = request.params["old_{colName}".format(colName=key)].rstrip().lstrip()
			updRowId = int(request.params["id"].rstrip().lstrip())

			existingRow = {key: newName}
			existingRow = inserter.getRowByValue(**existingRow)
			mergeRow    = inserter.getRowByValue(dbId=updRowId)

			print("mergeRow=", mergeRow)
			print("existingRow=", existingRow)

			if key == "mtId" or key == "buId":

				try:
					int(newName)
				except ValueError:
					traceback.print_exc()
					print("Values = '%s', '%s'" % (newName))
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
		print(request.params)

		if not "new-rating" in request.params:
			return Response(body=json.dumps({"Status": "Failed", "Message": "No new rating specified in rating-change call!"}))

		mangaName = request.params["change-rating"]
		newRating = request.params["new-rating"]

		try:
			newRating = int(newRating)
		except ValueError:
			return Response(body=json.dumps({"Status": "Failed", "Message": "New rating was not a integer!"}))

		if not mangaName in nt.dirNameProxy:
			return Response(body=json.dumps({"Status": "Failed", "Message": "Specified Manga Name not in dir-dict."}))

		print("Calling ratingChange")
		nt.dirNameProxy.changeRating(mangaName, newRating)
		print("ratingChange Complete")

		return Response(body=json.dumps({"Status": "Success", "Message": "Directory Renamed"}))

	def resetDownload(self, request):
		print(request.params)

		dbId = mangaName = request.params["reset-download"]

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



	def handleApiCall(self, request):

		print("API Call!", request.params)

		if request.remote_addr in settings.noHighlightAddresses:
			return Response(body=json.dumps({"Status": "Failed", "Message": "API calls are blocked from the reverse-proxy IP."}))


		if "change-rating" in request.params:
			print("Rating change!")
			return self.changeRating(request)

		elif "update-series" in request.params:
			print("Update series!")
			return self.updateSeries(request)

		elif "reset-download" in request.params:
			print("Download Reset!")
			return self.resetDownload(request)

		else:
			return Response(body="wat?")
