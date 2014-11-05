

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

	# If getMatchingArchives returns something, it means we're /not/ unique,
	# because getMatchingArchives returns matching files
	def isBinaryUnique(self):
		ret = self.getMatchingArchives()

		if len(ret):
			return False
		return True

	def isPhashUnique(self, searchDistance=PHASH_DISTANCE_THRESHOLD):
		ret = self.getPhashMatchingArchives(searchDistance)

		if len(ret):
			return False
		return True


	def getBestBinaryMatch(self):
		ret = self.getMatchingArchives()
		return self._getBestMatchingArchive(ret)

	def getBestPhashMatch(self, distance=PHASH_DISTANCE_THRESHOLD):
		ret = self.getPhashMatchingArchives(distance)
		return self._getBestMatchingArchive(ret)

	# "Best" match is kind of a fuzzy term here. I define it as the archive with the
	# most files in common with the current archive.
	# If there are multiple archives with identical numbers of items in common,
	# the "best" is then the largest of those files
	# (I assume that the largest is probably either a 1. volume archive, or
	# 2. higher quality)
	def _getBestMatchingArchive(self, ret):
		# Short circuit for no matches
		if not len(ret):
			return None

		tmp = {}
		for key in ret.keys():
			tmp.setdefault(len(ret[key]), []).append(key)

		maxKey = max(tmp.keys())

		# If there is only one file with the most items, return that.
		if len(tmp[maxKey]) == 1:
			return tmp[maxKey].pop()

		items = [(os.path.getsize(item), item) for item in tmp[maxKey]]
		items.sort()

		# Finally, sort by size, return the biggest one of them
		return items.pop()[-1]


	def getMatchingArchives(self):
		self.log.info("Checking if %s contains any unique files.", self.archPath)

		matches = {}
		for dummy_fileN, fileCtnt in self.arch:
			hexHash = self.remote.root.getMd5Hash(fileCtnt.read())

			dupsIn = self.db.getOtherHashes(hexHash, fsMaskPath=self.archPath)
			dups = []
			for fsPath, internalPath, dummy_itemhash in dupsIn:
				if os.path.exists(fsPath):

					matches.setdefault(fsPath, set()).add(internalPath)
					dups.append((fsPath, internalPath, dummy_itemhash))
				else:
					self.log.warn("Item '%s' no longer exists!", fsPath)
					self.db.deleteBasePath(fsPath)

			# Short circuit on unique item, since we are only checking if ANY item is unique
			if not dups:
				self.log.info("It contains at least one unique files.")
				return {}

		self.log.info("It does not contain any unique files.")

		return matches


	def getPhashMatchingArchives(self, searchDistance=PHASH_DISTANCE_THRESHOLD):

		# self.db.deleteBasePath(self.archPath)

		self.log.info("Scanning for phash duplicates.")
		matches = {}

		for fileN, fileCtnt in self.arch:
			dummy_fName, dummy_hexHash, pHash, dummy_dHash, dummy_imX, dummy_imY = self.remote.root.hashFile(self.archPath, fileN, fileCtnt.read())


			proximateFiles = self.db.getWithinDistance(pHash, searchDistance)
			self.log.info("File: '%s', '%s'. Number of matches %s", self.archPath, fileN, len(proximateFiles))

			dups = []

			for row in [match for match in proximateFiles if match]:
				fsPath, internalPath = row[1], row[2]
				if os.path.exists(fsPath):

					matches.setdefault(fsPath, set()).add(internalPath)
					dups.append((fsPath, internalPath, dummy_hexHash))
				else:
					self.log.warn("Item '%s' no longer exists!", fsPath)
					self.db.deleteBasePath(fsPath)


			# Short circuit on unique item, since we are only checking if ANY item is unique
			if len(dups) == 0:
				print("Wat?")
			if len(matches) == 0:
				print("WatWAT?")
			if not dups:
				self.log.info("Archive contains at least one unique phash(es).")
				return {}

		self.log.info("Archive does not contain any unique phashes.")
		return matches




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

	# Proxy through to the archChecker from UniversalArchiveReader
	@staticmethod
	def isArchive(archPath):
		return UniversalArchiveReader.ArchiveReader.isArchive(archPath)

def go():

	import logSetup
	logSetup.initLogging()
	print("Running")
	checker = ArchChecker("/media/Storage/Manga/Junketsu No Maria [+]/Junketsu no Maria v01 c02[fbn].zip")
	ret = checker.getBestBinaryMatch()
	print("Bin Match", ret)
	ret = checker.getBestPhashMatch()
	print("Phs Match", ret)
	# checker.addNewArch()


if __name__ == "__main__":
	go()

