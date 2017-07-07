import os.path

import time
import processDownload
import nameTools as nt
import shutil
import settings
import DbBase
import rpyc
import signal
import traceback
import os
import deduplicator.archChecker

class UntaggableError(RuntimeError):
	pass

class DirDeduper(DbBase.DbBase):


	def addTag(self, srcPath, newTags):
		# Don't do anything if we're not actually doing anything.
		if newTags == '':
			return

		with self.context_cursor() as cur:

			tagsets = []
			rowIds = []

			cur.execute("BEGIN;")
			basePath, fName = os.path.split(srcPath)
			# print("fname='%s', path='%s'" % (fName, basePath))
			query = '''SELECT dbId, tags FROM {tableName} WHERE fileName=%s AND downloadPath=%s;'''.format(tableName=self.tableName)
			print("Query: '%s'" % query)
			cur.execute(query, (fName, basePath))
			rows = cur.fetchall()
			print("Rows: '%s'" % rows)
			if len(rows) >= 1:
				exists = 0
				for rowid, tagsTmp in rows:

					if tagsTmp is None:
						tagsTmp = ''
					if not any([tmp in tagsTmp for tmp in ["deleted", "duplicate"]]):
						exists += 1
						rowIds.append(rowid)

					tagsets.append(tagsTmp)

			else:
				self.log.info("File {fname} not in manga database!".format(fname=srcPath))
				return

			if not rowIds:
				self.log.warning("Could not add tag to row that does not exist!")
				self.log.warning("Path: '%s'", srcPath)
				self.log.warning("New tags: '%s'", newTags)

				raise UntaggableError("Could not add tag to row that does not exist!")

			for tags, rowId in zip(tagsets, rowIds):
				if tags is None:
					tags = ''
				tags = set(tags.split())
				for tag in newTags.split():
					if tag:
						tags.add(tag)

				tags = [tag.lower() for tag in tags]
				tags.sort()
				cur.execute('''UPDATE {tableName} SET tags=%s WHERE dbId=%s;'''.format(tableName=self.tableName), (" ".join(tags), rowId))
			cur.execute("COMMIT;")


	def removeTag(self, dbid, deltag):

		with self.transaction() as cur:
			cur.execute('''SELECT dbId, tags FROM {tableName} WHERE dbid=%s;'''.format(tableName=self.tableName), (dbid, ))
			rows = cur.fetchall()
			assert len(rows) == 1
			dbid, tags = rows[0]
			tags = tags.split(" ")
			tags.remove(deltag)

			tags = [tag.lower() for tag in tags]
			tags.sort()

			cur.execute('''UPDATE {tableName} SET tags=%s WHERE dbId=%s;'''.format(tableName=self.tableName), (" ".join(tags), dbid))
			print("Item return:", dbid, tags)


	def setupDbApi(self):
		pass

	def cleanDirectory(self, dirPath, includePhash=False, pathPositiveFilter=None):

		self.log.info("Cleaning path '%s'", dirPath)
		items = os.listdir(dirPath)
		items.sort()
		for item in items:
			item = os.path.join(dirPath, item)
			if os.path.isdir(item):
				print("Scanning", item)
				self.cleanSingleDir(item, includePhash, pathPositiveFilter)


	def __process_download(self, basePath, pathPositiveFilter):
		if settings.mangaCmsHContext in os.path.abspath(basePath):
			processor = processDownload.HentaiProcessor
		else:
			processor = processDownload.MangaProcessor

		failures = 0
		while True:
			try:
				self.log.info("Scanning '%s'", basePath)

				proc = processor()
				tags = proc.processDownload(seriesName=None, archivePath=basePath, pathPositiveFilter=pathPositiveFilter)
				tags += " dup-checked"
				self.addTag(basePath, tags)
				return
			except EOFError:
				self.log.error("EOF Error: %s", failures)
				failures += 1
				time.sleep(3)
				if failures > 50:
					raise
			except ConnectionRefusedError:
				self.log.error("ConnectionRefusedError: %s", failures)
				failures += 1
				time.sleep(3)
				if failures > 50:
					raise

			except UntaggableError as e:
				self.log.error("UntaggableError: %s", e)
				return

			except KeyboardInterrupt:
				raise


	def cleanSingleDir(self, dirPath, includePhash=True, pathPositiveFilter=None):

		self.log.info("Processing subdirectory '%s'", dirPath)
		if not dirPath.endswith("/"):
			dirPath = dirPath + '/'

		items = os.listdir(dirPath)

		items = [os.path.join(dirPath, item) for item in items]

		dirs = [i for i in items if os.path.isdir(i)]
		self.log.info("Recursing into %s subdirectories!", len(dirs))
		for subDir in dirs:
			self.cleanSingleDir(subDir, includePhash, pathPositiveFilter)


		parsedItems = [(os.path.getsize(i), i) for i in items if os.path.isfile(i)]

		parsedItems.sort()


		for dummy_num, basePath in parsedItems:
			self.__process_download(basePath, pathPositiveFilter)

	def cleanBySourceKey(self, sourceKey, includePhash=True, pathPositiveFilter=None):

		self.log.info("Getting fetched items from database for source: %s", sourceKey)
		with self.context_cursor() as cur:
			cur.execute('''SELECT dbid, filename, downloadpath, tags FROM mangaitems WHERE sourcesite=%s and dlstate=2;''', (sourceKey, ))
			ret = cur.fetchall()
		self.log.info("Found %s items from source %s.", len(ret), sourceKey)

		skipped = 0

		for dbid, filename, downloadpath, tags in ret:
			if not tags:
				tags = ""

			taglist = tags.split()

			fpath = os.path.join(downloadpath, filename)

			if tags and 'dup-checked' in taglist:
				# self.log.info("File %s was dup-checked in the current session. Skipping.", fpath)
				skipped += 1
				if skipped % 100 == 0:
					self.log.info("Skipped %s items", skipped)
				continue

			if tags and 'was-duplicate' in taglist:
				continue

			if not filename or not downloadpath:
				self.log.error("Invalid path info: '%s', '%s'", downloadpath, filename)


			if not os.path.exists(fpath):
				continue


			proc = processDownload.MangaProcessor()
			tags = proc.processDownload(seriesName=None, archivePath=fpath, doUpload=False)
			tags += " dup-checked"
			self.log.info("Adding tags: '%s'", tags)
			self.addTag(fpath, tags)


	def fixSwap(self):
		self.log.info("Fixing swapped paths for %s.", self.tableName)
		mismatch_ids = set()
		with self.context_cursor() as cur:
			cur.execute("""SELECT dbid, sourcesite, filename, downloadpath
							FROM {tableName} WHERE dlstate=2 AND filename IS NOT NULL AND downloadpath IS NOT NULL ORDER BY dbid ASC""".format(tableName=self.tableName))
			ret = cur.fetchall()

		for dbid, sourcesite, filename, downloadpath in ret:

			if filename.startswith("/"):   # So... these are getting swapped. Somehow.

				with self.context_cursor() as cur:
					self.log.warning("File has path and filename swapped! Source: %s, fname: '%s', fpath: '%s'", sourcesite, filename, downloadpath)
					mismatch_ids.add(sourcesite)

					cur.execute("""UPDATE
										{tableName}
									SET
										filename = %s, downloadpath = %s
									WHERE
										dbid = %s;""".format(tableName=self.tableName),
								(downloadpath, filename, dbid))
					print(cur.rowcount)
					cur.execute("COMMIT;")
			else:
				fqp = os.path.join(downloadpath, filename)
				absp = os.path.abspath(fqp)
				ndl, nf = os.path.split(absp)
				if not any([downloadpath == ndl, filename == nf]):
					print(downloadpath == ndl, filename == nf)

		self.log.info("Mismatching plugins: %s", mismatch_ids)
	def cleanHistory(self):


		pathPositiveFilter = None


		self.log.info("Querying for items.")

		with self.context_cursor() as cur:
			cur.execute("""SELECT dbid, sourcesite, filename, downloadpath, tags
							FROM {tableName} WHERE dlstate=2 AND filename IS NOT NULL AND downloadpath IS NOT NULL ORDER BY dbid ASC""".format(tableName=self.tableName))
			ret = cur.fetchall()

		self.log.info("Found %s items. Loading.", len(ret))

		ret = [(dbid, sourcesite, filename, downloadpath, tags) for dbid, sourcesite, filename, downloadpath, tags in ret]
		self.log.info("Items loaded. Processing.")
		skipped = 0

		for dbid, sourcesite, filename, downloadpath, tags in ret:
			if not tags:
				tags = ""

			taglist = tags.split()

			if downloadpath.startswith("/"):
				fpath = os.path.join(downloadpath, filename)
			elif filename.startswith("/"):   # So... these are getting swapped. Somehow.
				self.log.warning("File has path and filename swapped! Source: %s", sourcesite)
				raise RuntimeError("File has path and filename swapped! Source: %s" % sourcesite)
			else:
				raise RuntimeError("File has path and filename swapped! Source: %s" % sourcesite)

			if tags and 'dup-checked' in taglist or 'missing-file' in taglist:
				# self.log.info("File %s was dup-checked in the current session. Skipping.", fpath)
				skipped += 1
				if skipped % 100 == 0:
					self.log.info("Skipped %s items", skipped)
				continue

			if tags and 'was-duplicate' in taglist:
				skipped += 1
				continue

			self.log.info("Item %s - DownloadPath: '%s', filename: '%s'", dbid, downloadpath, filename)


			if not filename or not downloadpath:
				self.log.error("Invalid path info: '%s', '%s'", downloadpath, filename)

			if not os.path.exists(fpath):
				self.log.warning("File for item seems to be missing!")
				self.addTag(fpath, 'missing-file')
				continue

			if not os.path.isfile(fpath):
				self.log.error("Path is not a file! Path: '%s', File: '%s'", downloadpath, filename)
				self.log.error("Joined path: '%s'", fpath)
				continue

			with self.context_cursor() as cur:
				cur.execute('''SELECT dbId FROM {tableName} WHERE fileName=%s AND downloadPath=%s;'''.format(tableName=self.tableName), (filename, downloadpath))
				haver1 = cur.fetchall()

				basePath, fName = os.path.split(fpath)
				cur.execute('''SELECT dbId FROM {tableName} WHERE fileName=%s AND downloadPath=%s;'''.format(tableName=self.tableName), (fName, basePath))
				haver2 = cur.fetchall()

			if not haver1:
				self.log.error("Querying for file failed from source 1?")
				continue
				# raise RuntimeError("Requery for file failed: %s" % sourcesite)
			if not haver2:
				self.log.error("Querying for file failed from source 2?")
				continue
				# raise RuntimeError("Round-tripping through os.path.join failed: %s" % sourcesite)


			self.__process_download(fpath, pathPositiveFilter)



	def globalRemoveTag(self, bad_tag):
		assert bad_tag

		self.log.info("Querying for items.")
		with self.context_cursor() as cur:
			cur.execute("SELECT dbid, filename, downloadpath, tags FROM hentaiitems ORDER BY dbid ASC")
			ret = cur.fetchall()


		for dbid, filename, downloadpath, tags in ret:
			if not all([filename, downloadpath, tags]):
				continue
			taglist = tags.split()
			fpath = os.path.join(downloadpath, filename)
			if not taglist:
				continue
			if not bad_tag in taglist:
				continue

			self.log.info("Stripping tag from %s", fpath)
			self.removeTag(dbid, bad_tag)
		self.log.info("Scanned %s rows", len(ret))

	def purgeDedupTempsMd5Hash(self, dirPath):

		self.remote = rpyc.connect("localhost", 12345)
		self.db = self.remote.root.DbApi()

		self.log.info("Cleaning path '%s'", dirPath)
		items = os.listdir(dirPath)
		for itemInDelDir in items:

			fqPath = os.path.join(dirPath, itemInDelDir)
			try:
				dc = deduplicator.archChecker.ArchChecker(fqPath)
				fileHashes = dc.getHashes(shouldPhash=False)
			except ValueError:
				self.log.critical("Failed to create archive reader??")
				self.log.critical(traceback.format_exc())
				self.log.critical("File = '%s'", fqPath)
				self.log.critical("Skipping file")
				continue

			# Get all the hashes for every file /but/ any that are windows Thumbs.db files.
			itemHashes = set([item[1] for item in fileHashes if not item[0].endswith("Thumbs.db")])

			matches = [self.db.getByHash(fHash) for fHash in itemHashes]

			if not all(matches):
				self.log.error("Missing match for file '%s'", itemInDelDir)
				self.log.error("Skipping")
				continue

			badMatch = [match for match in matches if fqPath in match[0]]

			files = set([subitem[0] for item in matches for subitem in item])

			exists = []
			for item in files:
				if os.path.exists(item):
					exists.append(True)
				else:
					exists.append(False)
					self.log.warn("File no longer seems to exist: '%s'!", item)
					self.log.warn("Deleting from database")
					try:
						self.db.deleteDbRows(fspath=item)
					except KeyError:
						self.log.error("Key error when deleting. Already deleted?")

			# Check the SHIT OUTTA DAT
			# Check if all items in the DB exist,
			# print("allExist", all(allExist))

			self.log.info("AllMatched = '%s'", all(matches))
			self.log.info("allExist = '%s'", all(exists))
			self.log.info("haveBad = '%s'", any(badMatch))

			if all(matches) and all(exists) and not any(badMatch):
				self.log.info("Should delete!")

				self.log.critical("DELETING '%s'", fqPath)
				os.unlink(fqPath)

			else:
				self.log.critical("Scan failed? '%s'", itemInDelDir)
				self.log.critical("AllMatched = '%s'", all(matches))
				self.log.critical("allExist = '%s'", all(exists))
				self.log.critical("haveBad = '%s'", any(badMatch))


	def restoreDirectory(self, dirPath):


		self.log.info("Restoring path '%s'", dirPath)
		items = os.listdir(dirPath)
		items.sort()
		for item in items:
			split = len(item)
			while True:
				try:
					newName = item[:split].replace(";", "/")+item[split:]
					shutil.move(os.path.join(dirPath, item), os.path.join("/media/Storage/MP", newName))
					break
				except FileNotFoundError:
					print("ERR", newName)
					split -= 1
			print("item = ", newName)

	def reprocessFailedH(self):

		with self.context_cursor() as cur:
			cur.execute('''SELECT dbid, filename, downloadpath, tags FROM hentaiitems WHERE tags LIKE %s;''', ('%unprocessable%', ))
			ret = cur.fetchall()
		for dbid, fname, dpath, tags in ret:
			basePath = os.path.join(dpath, fname)

			tags = tags.split(" ")
			badtags = ['unprocessable', 'corrupt']
			for bad in badtags:
				while bad in tags:
					tags.remove(bad)
			print(os.path.exists(basePath), basePath)
			print(tags)

			proc = processDownload.MangaProcessor()
			tags = proc.processDownload(seriesName=None, archivePath=basePath, pathPositiveFilter=None)
			self.addTag(basePath, tags)


	def moveUnlinkableDirectories(self, dirPath, toPath):


		print("Moving Unlinkable from", dirPath)
		print("To:", toPath)
		if not os.path.isdir(dirPath):
			print(dirPath, "is not a directory")
			raise ValueError
		if not os.path.isdir(toPath):
			print(toPath, "is not a directory")
			raise ValueError

		srcItems = os.listdir(dirPath)
		srcItems.sort()
		print("Len ", len(srcItems))
		for item in srcItems:
			itemPath = os.path.join(dirPath, item)
			if not os.path.isdir(itemPath):
				continue

			if not nt.haveCanonicalMangaUpdatesName(item):
				targetDir = os.path.join(toPath, item)
				print("Moving item", item, "to unlinked dir")
				shutil.move(itemPath, targetDir)


		srcItems = os.listdir(toPath)
		srcItems.sort()
		print("Len ", len(srcItems))
		for item in srcItems:
			itemPath = os.path.join(toPath, item)
			if not os.path.isdir(itemPath):
				continue

			if nt.haveCanonicalMangaUpdatesName(item):
				print("Moving item", item, "to linked dir")
				targetDir = os.path.join(dirPath, item)
				shutil.move(itemPath, targetDir)
			else:
				mId = nt.getAllMangaUpdatesIds(item)
				if mId:
					print("Item has multiple matches:", itemPath)
					for no in mId:
						print("	URL: https://www.mangaupdates.com/series.html?id=%s" % (no, ))

	# This is implemented as a separate codepath from the mormal dir dedup calls as a precautionary measure against
	# stupid coding issues. It's not a perfect fix, but it's better then nothing.
	def purgeDupDirPhash(self, dirPath):

		self.remote = rpyc.connect("localhost", 12345)
		self.db = self.remote.root.DbApi()

		items = os.listdir(dirPath)
		items = [os.path.join(dirPath, item) for item in items]
		items = [item for item in items if os.path.isfile(item)]

		for fileName in items:
			isDup = self.checkIfNotUnique(fileName)
			if isDup:
				self.log.critical("DELETING '%s'", fileName)
				os.unlink(fileName)

	def checkIfNotUnique(self, fileName):
		'''
		Check if item `filename` in the currently open archive is unique

		Returns True if item not unique, False if it is unique
		'''

		dc = deduplicator.archChecker.ArchChecker(fileName)
		try:
			hashes = dc.getHashes(shouldPhash=True)
		except Exception:
			self.log.error("Error when scanning item!")
			self.log.error("File: '%s'", fileName)
			self.log.error(traceback.format_exc())
			return False

		for hashVal in hashes:
			if hashVal[2] == None:

				if hashVal[0].endswith("Thumbs.db"):
					self.log.info("Windows Thumbs.db file")
					continue

				if hashVal[0].endswith("deleted.txt"):
					self.log.info("Advert Deletion note.")
					continue

				self.log.info("Empty hash: '%s', for file '%s'", hashVal[2], hashVal)
				return False

			if hashVal[2] == 0:
				self.log.info("Stupidly common hash (%s). Skipping", hashVal[2])
				continue

			matches = self.db.getWithinDistance(hashVal[2], wantCols=['dbId', 'fspath'])


			exists = [os.path.exists(item[1]) for item in matches]

			# if we have no returned rows, or none of the returned rows exist, return false
			if not len(exists) or not any(matches):
				return False

		return True



class MDirDeduper(DirDeduper):
	loggerPath = "Main.MDirDedup"
	tableName  = "MangaItems"
	pluginName = "MDirDeduper"


class HDirDeduper(DirDeduper):
	loggerPath = "Main.HDirDedup"
	tableName  = "HentaiItems"
	pluginName = "HDirDeduper"


def runRestoreDeduper(sourcePath):

	dd = MDirDeduper()
	dd.setupDbApi()
	dd.restoreDirectory(sourcePath)



def runMDeduper():

	dd = MDirDeduper()
	dd.setupDbApi()
	dd.cleanHistory()

def fixSwap():

	dd = MDirDeduper()
	dd.setupDbApi()
	dd.fixSwap()

	dd = HDirDeduper()
	dd.setupDbApi()
	dd.fixSwap()



def runSrcDeduper(sourceKey):

	dd = MDirDeduper()
	dd.setupDbApi()
	dd.cleanBySourceKey(sourceKey)



def runKissDeduper():

	runSrcDeduper("ki")


def runHDeduper():

	dd = HDirDeduper()
	dd.setupDbApi()
	dd.cleanHistory()


def resetDeduperScan():

	dd = HDirDeduper()
	dd.globalRemoveTag('dup-checked')
	dd = MDirDeduper()
	dd.globalRemoveTag('dup-checked')




def purgeDedupTemps(basePath):

	dd = MDirDeduper()
	dd.setupDbApi()
	dd.purgeDedupTempsMd5Hash(basePath)


def purgeDedupTempsPhash(basePath):

	dd = MDirDeduper()
	dd.setupDbApi()
	dd.purgeDupDirPhash(basePath)


def moveUnlinkable(dirPath, toPath):

	dd = MDirDeduper()
	dd.setupDbApi()
	dd.moveUnlinkableDirectories(dirPath, toPath)


def runSingleDirDeduper(dirPath, deletePath):

	dd = MDirDeduper()
	dd.setupDbApi()
	if not os.path.isdir(dirPath):
		raise ValueError("Passed path is not a directory! Path: '%s'" % dirPath)

	dd.cleanSingleDir(dirPath, deletePath)






def reprocessHFailed():

	dd = MDirDeduper()
	dd.setupDbApi()
	dd.reprocessFailedH()



if __name__ == '__main__':
	import logSetup
	logSetup.initLogging()

	dd = HDirDeduper()
	dd.globalRemoveTag("dup-checked")


