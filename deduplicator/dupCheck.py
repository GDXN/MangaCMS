
import hashlib

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
			fMD5 = hashlib.md5()
			fMD5.update(fileCtnt.read())
			hexHash = fMD5.hexdigest()

			dups = self.db.getOtherHashes(hexHash, fsMaskPath=self.archPath)

			# Short circuit on unique item, since we are only checking if ANY item is unique
			if not dups:
				self.log.info("It contains at least one unique files.")
				return True

				self.log.info("It does not contain any unique files.")
		return False

	def deleteArch(self):

		print("Deleting archive", self.archPath)

		self.db.deleteBasePath(self.archPath)
		os.remove(self.archPath)

	def addNewArch(self):

		self.log.info("Hashing file %s" % self.archPath)
		archIterator = UniversalArchiveReader.ArchiveReader(self.archPath)

		for fName, fp in archIterator:

			fCont = fp.read()
			fName, hexHash, pHash, dHash = self.hashModule.hashFile(self.archPath, fName, fCont)

			baseHash, oldPHash, oldDHash = self.db.getHashes(self.archPath, fName)
			if all((baseHash, oldPHash, oldDHash)):
				self.log.critical("Already hashed item?")
				self.log.critical("%s, %s, %s, %s, %s", self.archPath, fName, hexHash, pHash, dHash)

			if baseHash:
				self.db.updateItem(self.archPath, fName, hexHash, pHash, dHash)
			else:
				self.db.insertItem(self.archPath, fName, hexHash, pHash, dHash)

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

