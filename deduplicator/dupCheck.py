
from . import absImport
import settings
import UniversalArchiveReader
import os
import logging

# Checks an archive (`archPath`) against the contents of the database
# accessible via the `settings.dedupApiFile` python file, which
# uses the absolute-import tool in the current directory.

# check() returns True if the archive contains any unique items,
# false if it does not.

# deleteArch() deletes the archive which has path archPath,
# and also does the necessary database manipulation to reflect the fact that
# the archive has been deleted.
class ArchChecker(object):
	def __init__(self, archPath):
		self.archPath    = archPath
		self.arch        = UniversalArchiveReader.ArchiveReader(archPath)
		dbModule         = absImport.absImport(settings.dedupApiFile)
		self.hashModule  = absImport.absImport(settings.fileHasher)
		if not dbModule:
			raise ImportError
		self.db = dbModule.DbApi()
		self.log = logging.getLogger("Main.Deduper")

	def check(self):
		self.log.info("Checking if %s contains any unique files.", self.archPath)

		for dummy_fileN, fileCtnt in self.arch:
			hexHash = self.hashModule.getMd5Hash(fileCtnt.read())

			dupsIn = self.db.getOtherHashes(hexHash, fsMaskPath=self.archPath)
			dups = []
			for fsPath, internalPath, dummy_itemhash in dupsIn:
				if os.path.exists(fsPath):
					dups.append((fsPath, internalPath, dummy_itemhash))
				else:
					self.log.info("Item '%s' no longer exists - Removing from database!", fsPath)
					self.db.deleteBasePath(fsPath)

			# Short circuit on unique item, since we are only checking if ANY item is unique
			if not dups:
				self.log.info("It contains at least one unique files.")
				return True

		self.log.info("It does not contain any unique files.")
		return False

	def checkPhash(self):
		self.log.info("Checking if %s contains any unique files.", self.archPath)

		for fileN, fileCtnt in self.arch:
			dummy_fName, dummy_hexHash, pHash, dHash = self.hashModule.hashFile(self.archPath, fileN, fileCtnt.read())
			# print("Hashes", pHash, dHash, hexHash)
			dupsIn = self.db.getOtherDPHashes(dHash, pHash, fsMaskPath="LOLWATTTTTTTTT")
			dups = []
			for fsPath, internalPath, dummy_itemhash in dupsIn:
				if os.path.exists(fsPath):
					dups.append((fsPath, internalPath, dummy_itemhash))
				else:
					self.log.info("Item '%s' no longer exists - Removing from database!", fsPath)
					self.db.deleteBasePath(fsPath)


			# Short circuit on unique item, since we are only checking if ANY item is unique
			if not dups:
				self.log.info("It contains at least one unique files.")
				return True

		self.log.info("It does not contain any unique files.")
		return False

	def getHashes(self, shouldPhash=True):


		self.log.info("Getting item hashes for %s.", self.archPath)
		ret = []
		for fileN, fileCtnt in self.arch:
			ret.append(self.hashModule.hashFile(self.archPath, fileN, fileCtnt.read(), shouldPhash=shouldPhash))


		self.log.info("%s Fully hashed.", self.archPath)
		return ret

	def deleteArch(self):

		self.log.warning("Deleting archive '%s'", self.archPath)

		self.db.deleteBasePath(self.archPath)
		os.remove(self.archPath)

	def addNewArch(self, shouldPhash=True):

		self.log.info("Hashing file %s" % self.archPath)

		self.db.deleteBasePath(self.archPath)

		# Do overall hash of archive:
		with open(self.archPath, "rb") as fp:
			dummy_fName, hexHash, dummy_pHash, dummy_dHash = self.hashModule.hashFile(self.archPath, '', fp.read(), shouldPhash=False)
		self.db.insertItem(self.archPath, "", itemHash=hexHash)


		# Next, hash the file contents.
		archIterator = UniversalArchiveReader.ArchiveReader(self.archPath)
		for fName, fp in archIterator:

			fCont = fp.read()
			try:
				fName, hexHash, pHash, dHash = self.hashModule.hashFile(self.archPath, fName, fCont, shouldPhash=shouldPhash)

				baseHash, oldPHash, oldDHash = self.db.getHashes(self.archPath, fName)
				if all((baseHash, oldPHash, oldDHash)):
					self.log.warn("Item is not duplicate?")
					self.log.warn("%s, %s, %s, %s, %s", self.archPath, fName, hexHash, pHash, dHash)

				if baseHash:
					self.db.updateItem(self.archPath, fName, itemHash=hexHash, pHash=pHash, dHash=dHash)
				else:
					self.db.insertItem(self.archPath, fName, itemHash=hexHash, pHash=pHash, dHash=dHash)
			except IOError as e:
				self.log.error("Invalid/damaged image file in archive!")
				self.log.error("Archive '%s', file '%s'", self.archPath, fName)
				self.log.error("Error '%s'", e)

		self.db.commit()
		archIterator.close()

		self.log.info("File hashing complete.")

def go():

	import logSetup
	logSetup.initLogging()

	checker = ArchChecker("/media/Storage/MN/A Fairytale for the Demon Lord/A Fairytale for the Demon Lord Season 2 c00 - 23363-A_Fairytale_for_the_Demon_Lord_s2_ch00_Easy_Going.rar")
	checker.check()
	checker.addNewArch()


if __name__ == "__main__":
	module = go()

