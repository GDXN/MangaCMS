

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
				ret = json.dumps({"Status": "Success", "Message": "Updated Row!"})
			else:
				fromDict = {"dbId": updRowId}
				toDict = {"dbId": existingRow['dbId']}
				inserter.mergeItems(fromDict, toDict)
				ret = json.dumps({"Status": "Success", "Message": "Merged Rows!"})
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
			ret = "<a href='/books/book-item?title=%s'>%s</a>" % (urllib.parse.quote_plus(itemNameStr.encode("utf-8")), linkText)
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
		fqPath = os.path.abspath(fqPath)

		# Prevent path traversal crap.
		if not srcPathBase in fqPath:
			return Response(body=json.dumps({"Status": "Failed", "contents": "Nice path traversal try!"}))

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



	def addBookList(self, request):

		newList = request.params['listName']

		cur = self.conn.cursor()
		cur.execute("""SELECT COUNT(*) FROM book_series_lists WHERE listname=%s;""", (newList, ))
		ret = cur.fetchone()[0]

		if ret:
			return Response(body=json.dumps({"Status": "Failed", "contents": 'List already exists!'}))


		cur = self.conn.cursor()
		cur.execute("""INSERT INTO book_series_lists (listname) VALUES (%s);""", (newList, ))
		cur.execute('COMMIT')

		return Response(body=json.dumps({"Status": "Success", "contents": 'New list added!'}))


	def removeBookList(self, request):

		delList = request.params['listName']
		print("listname: '%s'" % delList)

		cur = self.conn.cursor()
		cur.execute("""SELECT COUNT(*) FROM book_series_lists WHERE listname=%s;""", (delList, ))
		ret = cur.fetchone()


		if not ret:
			print("List does not exist?")
			return Response(body=json.dumps({"Status": "Failed", "contents": 'Cannot delete list that doesn\'t exist!'}))


		cur = self.conn.cursor()
		cur.execute("""DELETE FROM book_series_lists WHERE listname=%s;""", (delList, ))
		cur.execute('COMMIT')

		return Response(body=json.dumps({"Status": "Success", "contents": 'List Deleted!'}))


	def setListForBook(self, request):
		bookId = request.params['set-list-for-book']
		listName = request.params['listName']

		if not listName:
			cur = self.conn.cursor()
			cur.execute("""DELETE FROM book_series_list_entries WHERE seriesid=%s;""", (bookId, ))

			return Response(body=json.dumps({"Status": "Success", "contents": 'Item list cleared!'}))


		# Check if the item already is in the list table.
		cur = self.conn.cursor()
		cur.execute("""SELECT COUNT(*) FROM book_series_list_entries WHERE seriesid=%s;""", (bookId, ))
		ret = cur.fetchone()[0]

		if ret:
			cur = self.conn.cursor()
			cur.execute("""UPDATE book_series_list_entries SET listname=%s WHERE seriesid=%s;""", (listName, bookId))
			cur.execute('COMMIT')

			return Response(body=json.dumps({"Status": "Success", "contents": 'Updated list for item!'}))


		cur = self.conn.cursor()
		cur.execute("""INSERT INTO book_series_list_entries (seriesid, listname) VALUES (%s, %s);""", (bookId, listName))
		cur.execute('COMMIT')

		return Response(body=json.dumps({"Status": "Success", "contents": 'Item list updated!'}))



	def setReadForBook(self, request):

		bookId = request.params['set-read-for-book']
		readChange = request.params['itemDelta']

		try:
			readChange = int(readChange)
		except ValueError:
			return Response(body=json.dumps({"Status": "Failed", "contents": 'Change value not an integer!'}))

		# Check if the item already is in the list table.
		cur = self.conn.cursor()
		cur.execute("""SELECT readingprogress FROM book_series WHERE dbid=%s;""", (bookId, ))
		retRow = cur.fetchone()
		if not retRow:
			return Response(body=json.dumps({"Status": "Failed", "contents": 'ID Not in database!'}))
		curRead = retRow[0]

		total = curRead + readChange
		if total < -1:
			total = -1

		cur.execute("""UPDATE book_series SET readingprogress=%s WHERE dbid=%s;""", (total, bookId))
		cur.execute('COMMIT')

		if total < 0:
			total = '-'
		ret = {
			"Status": "Success",
			"contents": 'Current read-to status: %s!' % total,
			"readTo": total
			}
		return Response(body=json.dumps(ret))

	def setRatingForBook(self, request):

		bookId = request.params["set-rating-for-book"]
		ratingStr = request.params["rating"]

		try:
			newRating = float(ratingStr)

			# Ratings are granular in 0.5 increments. Convert to integer fixed point (the db stores ints)
			newRating = newRating * 2
		except ValueError:
			return Response(body=json.dumps({"Status": "Failed", "contents": 'Change value not an integer!'}))

		cur = self.conn.cursor()
		cur.execute("""UPDATE book_series SET rating=%s WHERE dbid=%s;""", (newRating, bookId))
		cur.execute('COMMIT')

		ret = {
			"Status": "Success",
			"contents": 'Current rating status: %s!' % (newRating/0.5),
			}
		return Response(body=json.dumps(ret))

	def newCustomBook(self, request):

		assert request.params["new-custom-book"] == 'true'
		title = request.params["new-name"]


		cur = self.conn.cursor()
		cur.execute("""INSERT INTO book_series (itemname, itemtable) VALUES (%s, (SELECT dbid FROM book_series_table_links WHERE tablename=%s));""", (title, 'books_custom'))
		cur.execute('COMMIT')

		ret = {
			"Status": "Success",
			"contents": 'Inserted book: %s!' % title,
			}
		return Response(body=json.dumps(ret))


	def resetCrawlDist(self, request):

		assert request.params['reset-book-crawl-dist']
		assert request.params['western'] == 'false'
		rowid = int(request.params['reset-book-crawl-dist'])



		cur = self.conn.cursor()
		cur.execute("""UPDATE book_items SET distance=0 WHERE dbid=%s;""", (rowid, ))
		cur.execute('COMMIT')

		ret = {
			"Status": "Success",
			"contents": 'Reset crawl distance for item: %s!' % rowid,
			}
		return Response(body=json.dumps(ret))


	def resetDownloadState(self, request):

		assert request.params['reset-book-download-state']
		rowid = int(request.params['reset-book-download-state'])

		cur = self.conn.cursor()
		cur.execute("""UPDATE book_items SET distance=0, dlState=0 WHERE dbid=%s;""", (rowid, ))
		cur.execute('COMMIT')

		ret = {
			"Status": "Success",
			"contents": 'Reset crawl distance for item: %s!' % rowid,
			}
		return Response(body=json.dumps(ret))


	def deleteCustomBook(self, request):


		assert request.params["delete-custom-book"] == 'true'
		deleteId = request.params["delete-id"]


		cur = self.conn.cursor()
		cur.execute("""DELETE FROM book_series WHERE dbid=%s AND itemtable=(SELECT dbid FROM book_series_table_links WHERE tablename=%s);""", (deleteId, 'books_custom'))
		cur.execute('COMMIT')

		ret = {
			"Status": "Success",
			"contents": 'Item Deleted: %s!' % (deleteId),
			}
		return Response(body=json.dumps(ret))


	def handleApiCall(self, request):
		'''
		API Call handler.

		All API calls are done as GET requests. The response value is a JSON dictionary (or an error page).
		All response JSON objects will have a 'Status' Field, containing the literal string 'Success' if
		the API call was successful, or 'Failed' if it failed.
		Each response should also have a "contents" field, containing either the call's return value, or
		a human readable status message (for calls that permute server state, rather then do lookup)

		Available API Methods:
		 - "change-rating"
			Required parameters:
			 - "change-rating": Valid series name (e.g. something that can be looked up in the NT interface)
			 - "new-rating": The new rating of the series, as anything that will successfully cast to float()
			Updates the rating of a series by modifying the directory name.
			In general, it should only return a response once the update is complete. This isn't *completely*
			functional, though. There is some odd behaviour when directories are moved that I have not
			bothered to properly debug.

		 - "update-series"
			Required parameters:
			 - "old_buName"
			 - "old_mtName"
			 - "old_buId"
			 - "old_mtId"
			Used for cross-linking Mangaupdates and MangaTraders series.
			Basically useless, should probably be removed.

		 - "reset-download"
			Required parameters:
			 - "reset-download": database ID for the manga download to reset.
			Resets the download state of a item in the database. Only functions on a download with a dlState < 0,
			e.g. a failed download.

		 - "trigram-query-hentai-str"
			Required parameters:
			 - 'trigram-query-hentai-str': The name of the hentai to search for
			 - 'trigram-query-linktext': The string content of the returned link if the search returned results

			Do a trigram search (e.g. fuzzy text search) for a hentai title.
			'contents' contains HTML markup for a web-interface link to a page containing the search results, or
			"no entries found" text.


		 - "trigram-query-book-str"
			Required parameters:
			 - 'trigram-query-book-str': The name of the book to search for
			 - 'trigram-query-linktext': The string content of the returned link if the search returned results

			Do a trigram search (e.g. fuzzy text search) for a book title.
			'contents' contains HTML markup for a web-interface link to a page containing the search results, or
			"no entries found" text.

			Note: This is functionally identical to the behaviour of "trigram-query-hentai-str", aside from the table it searches.

		 - "delete-item"
			Required parameters:
			 - 'src-dict': The nt dictionary that the item is from
			 - 'src-path': the path of the item within the base path of the src-dict.

			Move an item to the recycle bin.

			The path is generated by taking the base path of the dict specified by 'src-dict',
			concatenating `src-path` onto it.

			The "deleted" item is then moved to the recycle bin directory specified in the settings.py file

		################################################################################
		# Book Management Stuff:
		################################################################################
		 - "add-book-list"
			Required parameters:
			 - 'listName'

		 - "remove-book-list"
		 - "set-list-for-book"
		 - "set-read-for-book"

		'''

		self.log.info("API Call! %s", request.params)

		if request.remote_addr in settings.noHighlightAddresses:
			return Response(body=json.dumps({"Status": "Failed", "contents": "API calls are blocked from the reverse-proxy IP."}))


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
		elif 'add-book-list' in request.params:
			return self.addBookList(request)
		elif 'remove-book-list' in request.params:
			return self.removeBookList(request)
		elif 'set-list-for-book' in request.params:
			return self.setListForBook(request)
		elif 'set-read-for-book' in request.params:
			return self.setReadForBook(request)
		elif "set-rating-for-book" in request.params:
			return self.setRatingForBook(request)

		elif "new-custom-book" in request.params:
			return self.newCustomBook(request)
		elif "delete-custom-book" in request.params:
			return self.deleteCustomBook(request)
		elif 'reset-book-crawl-dist' in request.params:
			return self.resetCrawlDist(request)
		elif 'reset-book-download-state' in request.params:
			return self.resetDownloadState(request)

		else:
			self.log.warning("Unknown API call")
			self.log.warning("Call params: '%s'", request.params)
			return Response(body=json.dumps({"Status": "Failed", "contents": "Unknown API Call.\nCall parameters: '%s'." % str(list(request.params.keys()))}))
