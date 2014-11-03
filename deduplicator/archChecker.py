

import UniversalArchiveReader
import os
import os.path
import logging
import rpyc

PHASH_DISTANCE_THRESHOLD = 2


class DbBase(object):
	def __init__(self):
		self.remote = rpyc.connect("localhost", 12345)
		self.db = self.remote.root.DbApi()

	def convertDbIdToPath(self, inId):
		return self.db.getItems(wantCols=['fsPath', "internalPath"], dbId=inId).pop()


class ArchChecker(DbBase):

	def __init__(self, archPath):
		super().__init__()


		self.archPath    = archPath
		self.arch        = UniversalArchiveReader.ArchiveReader(archPath)


		self.log = logging.getLogger("Main.Deduper")
		self.log.info("ArchChecker Instantiated")

	def isBinaryUnique(self):
		self.log.info("Checking if %s contains any unique files.", self.archPath)

		for dummy_fileN, fileCtnt in self.arch:
			hexHash = self.remote.root.getMd5Hash(fileCtnt.read())

			dupsIn = self.db.getOtherHashes(hexHash, fsMaskPath=self.archPath)
			dups = []
			for fsPath, internalPath, dummy_itemhash in dupsIn:
				if os.path.exists(fsPath):
					dups.append((fsPath, internalPath, dummy_itemhash))
				else:
					self.log.warn("Item '%s' no longer exists!", fsPath)
					# self.db.deleteBasePath(fsPath)

			# Short circuit on unique item, since we are only checking if ANY item is unique
			if not dups:
				self.log.info("It contains at least one unique files.")
				return True

		self.log.info("It does not contain any unique files.")
		return False


	def isPhashUnique(self, searchDistance=PHASH_DISTANCE_THRESHOLD):

		# self.db.deleteBasePath(self.archPath)

		self.log.info("Scanning for phash duplicates.")

		for fileN, fileCtnt in self.arch:
			dummy_fName, dummy_hexHash, pHash, dummy_dHash, dummy_imX, dummy_imY = self.remote.root.hashFile(self.archPath, fileN, fileCtnt.read())


			matches = self.db.getWithinDistance(pHash, searchDistance)
			self.log.info("File: '%s', '%s'. Matches '%s'", self.archPath, fileN, len(matches))

			dups = []

			for row in [match for match in matches if match]:
				fsPath, internalPath = row[1], row[2]
				# print("	'%s'" % ((row[1], row[2]), ))

				if os.path.exists(fsPath) and fsPath != self.archPath:
					dups.append((fsPath, internalPath))
				elif fsPath == self.archPath:
					pass
				else:
					self.log.info("Item '%s' no longer exists - Removing from database!", fsPath)
					self.log.warn("Existance check: %s", os.path.exists(fsPath))
					# self.db.deleteBasePath(fsPath)


			# Short circuit on unique item, since we are only checking if ANY item is unique
			if not dups:
				self.log.info("Archive contains at least one unique phash(es).")
				return True


		self.log.info("Archive does not contain any unique phashes.")
		return False






	def getHashes(self, shouldPhash=True):


		self.log.info("Getting item hashes for %s.", self.archPath)
		ret = []
		for fileN, fileCtnt in self.arch:
			ret.append(self.remote.root.hashFile(self.archPath, fileN, fileCtnt.read(), shouldPhash=shouldPhash))


		self.log.info("%s Fully hashed.", self.archPath)
		return ret

	def deleteArch(self):

		self.log.warning("Deleting archive '%s'", self.archPath)
		self.db.deleteBasePath(self.archPath)
		os.remove(self.archPath)


	def addNewArch(self, shouldPhash=True):

		self.log.info("Hashing file %s", self.archPath)

		self.db.deleteBasePath(self.archPath)

		# Do overall hash of archive:
		with open(self.archPath, "rb") as fp:
			hexHash = self.remote.root.getMd5Hash(fp.read())
		self.db.insertIntoDb(fspath=self.archPath, internalpath="", itemhash=hexHash)


		# Next, hash the file contents.
		archIterator = UniversalArchiveReader.ArchiveReader(self.archPath)
		for fName, fp in archIterator:

			fCont = fp.read()
			try:
				fName, hexHash, pHash, dHash, dummy_imX, dummy_imY = self.remote.root.hashFile(self.archPath, fName, fCont, shouldPhash=shouldPhash)

				baseHash, oldPHash, oldDHash = self.db.getHashes(self.archPath, fName)
				if all((baseHash, oldPHash, oldDHash)):
					self.log.warn("Item is not duplicate?")
					self.log.warn("%s, %s, %s, %s, %s", self.archPath, fName, hexHash, pHash, dHash)

				if baseHash:
					self.db.updateItem(fspath=self.archPath, internalpath=fName, itemHash=hexHash, pHash=pHash, dHash=dHash)
				else:
					self.db.insertIntoDb(fspath=self.archPath, internalpath=fName, itemHash=hexHash, pHash=pHash, dHash=dHash)


			except IOError as e:
				self.log.error("Invalid/damaged image file in archive!")
				self.log.error("Archive '%s', file '%s'", self.archPath, fName)
				self.log.error("Error '%s'", e)


		archIterator.close()

		self.log.info("File hashing complete.")



def go():

	import logSetup
	logSetup.initLogging()
	print("Running")
	checker = ArchChecker("/media/Storage/Manga/Junketsu No Maria [+]/Junketsu no Maria v01 c01[fbn].zip")
	checker.isPhashUnique()
	# checker.addNewArch()


if __name__ == "__main__":
	go()

