
from . import absImport
import settings
import logging
import runStatus
import sys
import os
import os.path
import shutil
import ScrapePlugins.DbBase

from contextlib import contextmanager

import time

try:
	import pyximport
	print("Have Cython")
	pyximport.install()

	import deduplicator.cyHamDb as hamDb
	print("Using cythoned hamming database system")

except ImportError:
	print("Deduplicator performance can be increased by")
	print("installing cython, which will result in the use of a ")
	print("cythonized database system")
	print("")

	print("Falling back to the pure-python implementation due to the lack of cython.")

	import deduplicator.hamDb as hamDb




PHASH_DISTANCE_THRESHOLD = 3

@contextmanager
def transaction(cursor, commit=True):
	if commit:
		cursor.execute("BEGIN;")

	try:
		yield

	except Exception as e:
		if commit:
			cursor.execute("ROLLBACK;")
		raise e

	finally:
		if commit:
			cursor.execute("COMMIT;")



class HamDb(ScrapePlugins.DbBase.DbBase):

	loggerPath = 'Main.Ham'



	def __init__(self):

		self.log = logging.getLogger("Main.Deduper")
		dbModule         = absImport.absImport(settings.dedupApiFile)

		self.db = dbModule.DbApi()
		self.hashtool = absImport.absImport(settings.fileHasher)

		self.log.info("Hamming Database opened.")
		self.hashTree = hamDb.BkHammingTree()
		self.openDB()

	def loadPHashes(self, pathPrefix=None):
		self.log.info("Loading PHashes")
		rowsIter = self.db.getPhashLikeBasePath(basePath=pathPrefix)
		self.log.info("Queried. %s results. Loading into tree.", len(rowsIter))

		totalItems = len(rowsIter)
		rowNum = 0

		start = time.time()

		for row in rowsIter:
			rowNum += 1
			dbId, pHash = row
			pHash = int(pHash, 2)


			if rowNum % 10000 == 0:
				self.log.info("Loading: On row %s, id = %s, hash = %s", rowNum, dbId, str(pHash).zfill(20))

				if not runStatus.run:
					self.log.info("Breaking due to exit flag being set")
					return

			self.hashTree.insert(pHash, dbId)

		end = time.time()


		self.log.info("All rows loaded! Total rows = %s", rowNum)


		delta = end-start
		self.log.info("Took %s seconds to load tree", delta)

	def getArchives(self, key):
		with self.conn.cursor() as cur:
			with transaction(cur):
				cur.execute('SELECT dbId, downloadPath, fileName, tags FROM hentaiitems WHERE sourceSite=%s;', (key, ))
				ret = cur.fetchall()
		self.log.info("Found %s archives to scan", len(ret))
		return ret

	def checkDuplicate(self, item):
		dbId, dirPath, fName, tags = item

		if "deleted" in tags:
			return

		fqPath = os.path.join(dirPath, fName)
		if not os.path.exists(fqPath):
			self.log.error("ORIGIN FILE IS MISSING! = '%s'", fqPath)
			return

		items = self.db.getItemsOnBasePath(fqPath)
		items = [item for item in items if item[1] != '']
		self.log.info("Have %s items for item %s", len(items), fName)

		itemIds = set([item[-1] for item in items])

		for item in items:
			extPath, intPath, fHash, pHash, dbId = item
			pHash = int(pHash, 2)
			matches = self.hashTree.getWithinDistance(pHash, PHASH_DISTANCE_THRESHOLD)


			# Remove any items corresponding to the item itself's ids
			matches -= itemIds

			# And then filter for any files that no longer exist on disk
			stillExist = []
			for dbId in list(matches):
				info = self.db.getById(dbId)
				if len(info) != 1:
					raise ValueError("Invalid ID? Wat?")

				itemPath = info[0][0]
				if os.path.exists(itemPath):
					stillExist.append(dbId)
				else:
					self.log.error("FILE IS MISSING = '%s'", info)


			if stillExist:
				# print(pHash, matches, stillExist)
				pass

			else:
				self.log.info("Item contains unique file. Skipping")
				return False # Short circuit on unique
		self.log.warning("Item is not unique!")
		return True



	# Insert new tags specified as a string kwarg (tags="tag Str") into the tags listing for the specified item
	def updateItemTags(self, dbId, tags):


		with self.conn.cursor() as cur:
			with transaction(cur):
				cur.execute('SELECT tags FROM hentaiitems WHERE dbId=%s;', (dbId, ))
				row = cur.fetchone()

		if not row:
			raise ValueError("Row specified does not exist!")

		tags = row[0]
		if tags:
			existingTags = set(tags.split(" "))
		else:
			existingTags = set()

		newTags = set(tags.split(" "))

		tags = existingTags | newTags

		tagStr = " ".join(tags)
		while "  " in tagStr:
			tagStr = tagStr.replace("  ", " ")

		with self.conn.cursor() as cur:
			with transaction(cur):
				cur.execute('UPDATE hentaiitems SET  tags=%s WHERE dbId=%s;', (tagStr, dbId))


	def moveItem(self, item, delPath):
		print("Item", item)
		dbId, dirPath, fName, dummy_tags = item

		srcPath = os.path.join(dirPath, fName)
		dstPath = os.path.join(delPath, item[-1])
		print("Should move from %s" % srcPath)
		print("              to %s" % dstPath)

		shutil.move(srcPath, dstPath)
		self.updateItemTags(dbId, "deleted was-duplicate phash-duplicate")


	def scanHistory(self, key, scanPath, delPath):
		self.loadPHashes(pathPrefix=scanPath)
		tocheck = self.getArchives(key)
		for item in tocheck:
			isDup = self.checkDuplicate(item)
			if isDup:
				self.moveItem(item, delPath)

	def loadTest(self, scanPath):
		self.loadPHashes(pathPrefix=scanPath)

def test():

	hint = HamDb()


	if len(sys.argv) < 2:
		print("This script requires command line parameters")
		print("'history-check {srcKey} {dirToScan} {deleteDir}'")

		return

	mainArg = sys.argv[1]

	print ("mode command = '%s'" % mainArg)

	if len(sys.argv) == 5:

		if mainArg.lower() == "history-check":
			key = sys.argv[2]
			scanPath = sys.argv[3]
			delPath = sys.argv[4]
			if os.path.exists(scanPath) and os.path.isdir(scanPath) and os.path.exists(delPath) and os.path.isdir(delPath):
				hint.scanHistory(key, scanPath, delPath)
			else:
				raise ValueError("Invalid arguments")
		else:
			print("Unknown arg!")


	if len(sys.argv) == 3:

		if mainArg.lower() == "load-test":
			scanPath = sys.argv[2]
			if os.path.exists(scanPath) and os.path.isdir(scanPath):
				hint.loadTest(scanPath)
			else:
				raise ValueError("Invalid arguments")
		else:
			print("Unknown arg!")

	else:
		print("Did not understand command line parameters")
		print("Arguments = ", sys.argv)




if __name__ == "__main__":
	import utilities.testBase
	with utilities.testBase.testSetup():
		test()

