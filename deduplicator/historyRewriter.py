
from . import absImport
import settings
import logging
import runStatus
import deduplicator.hamDb as hamDb
import sys
import os
import os.path

import ScrapePlugins.DbBase

from contextlib import contextmanager

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

		self.log.info("All rows loaded! Total rows = %s", rowNum)


	def getArchives(self, key):
		with self.conn.cursor() as cur:
			with transaction(cur):
				cur.execute('SELECT dbId, downloadPath, fileName FROM hentaiitems WHERE sourceSite=%s;', (key, ))
				ret = cur.fetchall()
		self.log.info("Found %s archives to scan", len(ret))
		return ret

	def checkDuplicate(self, item):
		dbId, dirPath, fName = item
		fqPath = os.path.join(dirPath, fName)
		if not os.path.exists(fqPath):
			return

		items = self.db.getItemsOnBasePath(fqPath)
		self.log.info("Have %s items for item %s", len(items), fName)


		# items = self.hashTree.getWithinDistance(targetHash, distance)

	def scanHistory(self, key, scanPath):
		# self.loadPHashes(pathPrefix=scanPath)
		tocheck = self.getArchives(key)
		for item in tocheck:
			self.checkDuplicate(item)


def test():

	hint = HamDb()


	if len(sys.argv) < 2:
		print("This script requires command line parameters")

		return

	mainArg = sys.argv[1]

	print ("mode command = '%s'" % mainArg)

	if len(sys.argv) == 4:

		if mainArg.lower() == "history-check":
			key = sys.argv[2]
			scanPath = sys.argv[3]
			if os.path.exists(scanPath) and os.path.isdir(scanPath):
				hint.scanHistory(key, scanPath)
			else:
				raise ValueError("Invalid arguments")
		else:
			print("Unknown arg!")
	else:
		print("Did not understand command line parameters")




if __name__ == "__main__":
	import utilities.testBase
	with utilities.testBase.testSetup():
		test()
