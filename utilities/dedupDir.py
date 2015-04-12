import os.path

import processDownload
import nameTools as nt
import shutil
import settings
import ScrapePlugins.DbBase
import rpyc
import signal
import traceback
import os
import deduplicator.archChecker


class DirDeduper(ScrapePlugins.DbBase.DbBase):
	loggerPath = "Main.DirDedup"
	tableName  = "MangaItems"


	def addTag(self, srcPath, newTags):
		with self.conn.cursor() as cur:

			tags = None
			rowId = None

			cur.execute("BEGIN;")
			basePath, fName = os.path.split(srcPath)
			# print("fname='%s', path='%s'" % (fName, basePath))
			cur.execute('''SELECT dbId, tags FROM {tableName} WHERE fileName=%s AND downloadPath=%s;'''.format(tableName=self.tableName), (fName, basePath))
			rows = cur.fetchall()
			if len(rows) > 1:
				exists = 0
				for row in rows:

					tagsTmp = row[1]
					if tagsTmp == None:
						tagsTmp = ''
					if not "deleted" in tagsTmp and not "missing" in tagsTmp and not "duplicate" in tagsTmp:
						exists += 1
						rowId = row[0]
						tags = row[1]


				if exists > 1:

					print("Rows")
					for row in rows:
						print(" = ", row)
						print(" = ", "deleted" in row, not "missing" in row, not "duplicate" in row)

					self.log.error("More then one row for the same path! Wat?")

					row = rows.pop()
					tags = row[1]
					rowId = row[0]

			elif rows:
				row = rows.pop()
				tags = row[1]
				rowId = row[0]
			else:
				self.log.info("File {fname} not in manga database!".format(fname=srcPath))
				return

			if not rowId:
				self.log.warning("WAt?")
				return

			if tags == None:
				tags = ''
			tags = set(tags.split())
			for tag in newTags.split():
				tags.add(tag.lower())

			cur.execute('''UPDATE {tableName} SET tags=%s WHERE dbId=%s;'''.format(tableName=self.tableName), (" ".join(tags), rowId))
			cur.execute("COMMIT;")

	def setupDbApi(self):
		pass

	def cleanDirectory(self, dirPath, delDir, includePhash=False, pathFilter=['']):

		self.log.info("Cleaning path '%s'", dirPath)
		items = os.listdir(dirPath)
		items.sort()
		for item in items:
			item = os.path.join(dirPath, item)
			if os.path.isdir(item):
				print("Scanning", item)
				self.cleanSingleDir(item, delDir, includePhash, pathFilter)



	def cleanSingleDir(self, dirPath, delDir, includePhash=True, pathFilter=['']):

		self.log.info("Processing subdirectory '%s'", dirPath)
		if not dirPath.endswith("/"):
			dirPath = dirPath + '/'

		items = os.listdir(dirPath)

		items = [os.path.join(dirPath, item) for item in items]

		dirs = [i for i in items if os.path.isdir(i)]
		self.log.info("Recursing into %s subdirectories!", len(dirs))
		for subDir in dirs:
			self.cleanSingleDir(subDir, delDir, includePhash, pathFilter)


		parsedItems = [(os.path.getsize(i), i) for i in items if os.path.isfile(i)]

		parsedItems.sort()


		for dummy_num, basePath in parsedItems:
			try:
				# if not deduplicator.archChecker.ArchChecker.isArchive(basePath):
				# 	print("Not archive!", basePath)
				# 	continue

				self.log.info("Scanning '%s'", basePath)

				proc = processDownload.MangaProcessor()
				tags = proc.processDownload(seriesName=None, archivePath=basePath, pathFilter=pathFilter)
				self.addTag(basePath, tags)

			except KeyboardInterrupt:
				raise

	def cleanBySourceKey(self, sourceKey, delDir, includePhash=True, pathFilter=['']):


		with self.conn.cursor() as cur:
			cur.execute('''SELECT dbid, filename, downloadpath FROM mangaitems WHERE sourcesite=%s;''', (sourceKey, ))
			ret = cur.fetchall()

		# print(ret)

		parsedItems = []
		for dbId, fName, fPath in ret:
			if not fName or not fPath:
				continue
			fqpath = os.path.join(fPath, fName)
			if not os.path.exists(fqpath):
				continue
			parsedItems.append((dbId, fqpath))

		for dummy_num, basePath in parsedItems:
			try:

				self.log.info("Scanning '%s'", basePath)

				proc = processDownload.MangaProcessor()
				tags = proc.processDownload(seriesName=None, archivePath=basePath, pathFilter=pathFilter)
				self.addTag(basePath, tags)

			except KeyboardInterrupt:
				raise

	def cleanHHistory(self, delDir):
		self.log.info("Querying for items.")
		with self.conn.cursor() as cur:
			cur.execute("SELECT dbid, filename, downloadpath, tags FROM hentaiitems ORDER BY dbid ASC")
			ret = cur.fetchall()

		for dbid, filename, downloadpath, tags in ret:

			if tags and 'was-duplicate' in tags.split():
				continue

			if not filename or not downloadpath:
				self.log.error("Invalid path info: '%s', '%s'", downloadpath, filename)

			fpath = os.path.join(downloadpath, filename)
			if not os.path.exists(fpath):
				continue

			proc = processDownload.HentaiProcessor()
			tags = proc.processDownload(seriesName=None, archivePath=fpath)
			self.log.info("Adding tags: '%s'", tags)
			self.addTag(fpath, tags)



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
			while (1):
				try:
					newName = item[:split].replace(";", "/")+item[split:]
					shutil.move(os.path.join(dirPath, item), os.path.join("/media/Storage/MP", newName))
					break
				except FileNotFoundError:
					print("ERR", newName)
					split -= 1
			print("item = ", newName)

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



class HDirDeduper(DirDeduper):
	loggerPath = "Main.HDirDedup"
	tableName  = "HentaiItems"


def runRestoreDeduper(sourcePath):

	dd = DirDeduper()
	dd.openDB()
	dd.setupDbApi()

	dd.restoreDirectory(sourcePath)

	dd.closeDB()

def runDeduper(basePath, deletePath):

	dd = DirDeduper()
	dd.openDB()
	dd.setupDbApi()

	dd.cleanDirectory(basePath, deletePath)

	dd.closeDB()

def runSrcDeduper(sourceKey, deletePath):

	dd = DirDeduper()
	dd.openDB()
	dd.setupDbApi()

	dd.cleanBySourceKey(sourceKey, deletePath)

	dd.closeDB()

def runHDeduper(deletePath):

	dd = HDirDeduper()
	dd.openDB()
	dd.setupDbApi()

	dd.cleanHHistory(deletePath)

	dd.closeDB()


def purgeDedupTemps(basePath):

	dd = DirDeduper()
	dd.openDB()
	dd.setupDbApi()
	dd.purgeDedupTempsMd5Hash(basePath)
	dd.closeDB()

def purgeDedupTempsPhash(basePath):

	dd = DirDeduper()
	dd.openDB()
	dd.setupDbApi()
	dd.purgeDupDirPhash(basePath)
	dd.closeDB()

def moveUnlinkable(dirPath, toPath):

	dd = DirDeduper()
	dd.openDB()
	dd.setupDbApi()
	dd.moveUnlinkableDirectories(dirPath, toPath)
	dd.closeDB()

def runSingleDirDeduper(dirPath, deletePath):

	dd = DirDeduper()
	dd.openDB()
	dd.setupDbApi()
	if not os.path.isdir(dirPath):
		raise ValueError("Passed path is not a directory! Path: '%s'" % dirPath)

	dd.cleanSingleDir(dirPath, deletePath)

	dd.closeDB()

