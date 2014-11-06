import os.path

import runStatus
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
			cur.execute("BEGIN;")
			basePath, fName = os.path.split(srcPath)
			# print("fname='%s', path='%s'" % (fName, basePath))
			cur.execute('''SELECT dbId, tags FROM MangaItems WHERE fileName=%s AND downloadPath=%s;''', (fName, basePath))
			rows = cur.fetchall()
			if len(rows) > 1:
				exists = 0
				for row in rows:

					tagsTmp = row[1]
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

			elif not rows:
				self.log.info("File {fname} not in manga database!".format(fname=srcPath))
				return
			else:
				row = rows.pop()
				tags = row[1]
				rowId = row[0]

			if tags == None:
				tags = ''
			tags = set(tags.split())
			for tag in newTags.split():
				tags.add(tag)

			cur.execute('''UPDATE MangaItems SET tags=%s WHERE dbId=%s;''', (" ".join(tags), rowId))
			cur.execute("COMMIT;")

	def setupDbApi(self):
		pass

	def cleanDirectory(self, dirPath, delDir):

		self.log.info("Cleaning path '%s'", dirPath)
		items = os.listdir(dirPath)
		items.sort()
		for item in items:
			item = os.path.join(dirPath, item)
			if os.path.isdir(item):
				self.cleanSingleDir(item, delDir)



	def cleanSingleDir(self, dirPath, delDir):

		self.log.info("Processing subdirectory '%s'", dirPath)
		if not dirPath.endswith("/"):
			dirPath = dirPath + '/'

		items = os.listdir(dirPath)



		items = [os.path.join(dirPath, item) for item in items]


		parsedItems = [(os.path.getsize(i), i) for i in items]

		parsedItems.sort()


		for dummy_num, basePath in parsedItems:
			try:
				if not deduplicator.archChecker.ArchChecker.isArchive(basePath):
					print("Not archive!", basePath)
					continue

				self.log.info("Scanning '%s'", basePath)

				ac = deduplicator.archChecker.ArchChecker(basePath)

				ret = ac.getBestBinaryMatch()
				if ret:
					self.log.info("Not Unique!")
					self.log.warning("Match for file '%s'", basePath)
					self.log.warning("Matching file '%s'", ret)


					dst = basePath.replace("/", ";")
					dst = os.path.join(delDir, dst)
					self.log.info("Moving item from '%s'", basePath)
					self.log.info("	to '%s'", dst)
					try:
						shutil.move(basePath, dst)

						self.addTag(basePath, "deleted was-duplicate")

						self.log.info("Not unique %s", basePath)
					except KeyboardInterrupt:
						raise
					except OSError:
						self.log.error("ERROR - Could not move file!")
						self.log.error(traceback.format_exc())

			except KeyboardInterrupt:
				raise
			except:
				print("Error processing file '%s'" % basePath)
				print("Traceback:")
				traceback.print_exc()
				print("")
				print("")


	def purgeDedupTemps(self, dirPath):

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


			itemHashes = set([item[1] for item in fileHashes])

			matches = [self.db.getByHash(fHash) for fHash in itemHashes]

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
					self.db.deleteDbRows(fspath=item)

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


		print("Move Unlinkable", dirPath, toPath)
		if not os.path.isdir(dirPath):
			print(dirPath, "is not a directory")
			raise ValueError
		if not os.path.isdir(toPath):
			print(toPath, "is not a directory")
			raise ValueError

		srcItems = os.listdir(dirPath)
		for item in srcItems:
			itemPath = os.path.join(dirPath, item)
			if not os.path.isdir(itemPath):
				continue
			if not nt.haveCanonicalMangaUpdatesName(item):
				targetDir = os.path.join(toPath, item)
				print("Moving item", item, "to unlinked dir")
				shutil.move(itemPath, targetDir)


		srcItems = os.listdir(toPath)
		for item in srcItems:
			itemPath = os.path.join(toPath, item)
			if not os.path.isdir(itemPath):
				continue
			if nt.haveCanonicalMangaUpdatesName(item):

				print("Moving item", item, "to linked dir")
				targetDir = os.path.join(dirPath, item)
				shutil.move(itemPath, targetDir)




def customHandler(dummy_signum, dummy_stackframe):
	if runStatus.run:
		runStatus.run = False
		print("Telling threads to stop")
	else:
		print("Multiple keyboard interrupts. Raising")
		raise KeyboardInterrupt

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


def purgeDedupTemps(basePath):

	dd = DirDeduper()
	dd.openDB()
	dd.setupDbApi()
	dd.purgeDedupTemps(basePath)
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


def test():

	signal.signal(signal.SIGINT, customHandler)

	runSingleDirDeduper("/media/Storage/Manga/National Quiz", '/media/Storage/rm')

if __name__ == "__main__":
	try:
		test()
	finally:
		pass
		# import nameTools as nt
		# nt.dirNameProxy.stop()

