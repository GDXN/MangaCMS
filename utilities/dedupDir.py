import sys
sys.path.insert(0,"..")
import os.path

import logSetup
if __name__ == "__main__":
	logSetup.initLogging()

import runStatus

import shutil
import settings
import ScrapePlugins.DbBase
import deduplicator.absImport
import signal
import traceback


def createLuts(inList):
	# Each item is 'fsPath,internalPath,itemhash'

	hashLUT = {}
	fileLUT = {}

	for fsPath, internalPath, itemhash in inList:
		if os.path.exists(fsPath):
			if itemhash in hashLUT:
				hashLUT[itemhash].append((fsPath, internalPath))
			else:
				hashLUT[itemhash] = [(fsPath, internalPath)]

			if fsPath in fileLUT:
				fileLUT[fsPath].append((internalPath, itemhash))
			else:
				fileLUT[fsPath] = [(internalPath, itemhash)]
		else:
			print("File deleted!", fsPath)
	return hashLUT, fileLUT


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
				self.log.warn("Do not have item {fname} in manga database!".format(fname=srcPath))
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
		dbModule         = deduplicator.absImport.absImport(settings.dedupApiFile)
		if not dbModule:
			raise ImportError
		self.db = dbModule.DbApi()


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
		items = self.db.getLikeBasePath(dirPath)

		hashLUT, fileLUT = createLuts(items)

		parsedItems = [(len(fileLUT[i]), i) for i in fileLUT.keys()]

		parsedItems.sort()

		for dummy_num, basePath in parsedItems:

			# print("Scanning ", basePath)
			containedFiles = fileLUT[basePath]
			itemItems = len(containedFiles)
			unique = []

			otherPaths = {}
			for internalPath, itemHash in containedFiles:

				# print("len", len(hashLUT[itemHash]), (internalPath, itemHash))

				if not itemHash in hashLUT:
					raise ValueError ("WAT")

				elif len(hashLUT[itemHash]) <= 1:
					unique.append((internalPath, itemHash))
				else:
					# print("internalPath", hashLUT[itemHash][1], internalPath)
					for fsPath, intPath in hashLUT[itemHash]:
						# print("fsPath, intPath", fsPath, " --/-- ", intPath)
						# print("internalPath", internalPath)
						if not fsPath == basePath:
							if fsPath in otherPaths:
								otherPaths[fsPath] += 1
							else:
								otherPaths[fsPath]  = 1


			if not unique:
				# print("Not Unique!", basePath)

				for internalPath, itemHash in containedFiles:
					hashLUT[itemHash].remove((basePath, internalPath))
					if len(hashLUT[itemHash]) == 0:
						hashLUT.pop(itemHash)



				dst = basePath.replace("/", ";")
				dst = os.path.join(delDir, dst)
				self.log.info("Moving item from '%s'", basePath)
				self.log.info("	to '%s'", dst)
				try:
					shutil.move(basePath, dst)

					self.addTag(basePath, "deleted was-duplicate")

					self.log.info("Not unique %s", basePath)
					self.log.info("Duplicated in :	")
					for oPath in [i for i in otherPaths.keys() if otherPaths[i] > 1]:
						self.log.info("		%s/%s: %s", otherPaths[oPath], itemItems, oPath)
					self.db.deleteBasePath(basePath)
				except KeyboardInterrupt:
					raise
				except OSError:
					self.log.error("ERROR - Could not move file!")
					self.log.error(traceback.format_exc())


			# else:
			# 	print("unique", basePath)


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

	runDeduper("wat")

if __name__ == "__main__":
	try:
		test()
	finally:
		pass
		# import nameTools as nt
		# nt.dirNameProxy.stop()

