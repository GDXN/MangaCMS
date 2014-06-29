
import hashlib

from . import absImport
import settings
import UniversalArchiveReader
import os

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
		self.archPath = archPath
		self.arch = UniversalArchiveReader.ArchiveReader(archPath)
		dbModule = absImport.absImport(settings.dedupApiFile)
		if not dbModule:
			raise ImportError
		self.db = dbModule.DbApi()

	def check(self):

		for dummy_fileN, fileCtnt in self.arch:
			fMD5 = hashlib.md5()
			fMD5.update(fileCtnt.read())
			hexHash = fMD5.hexdigest()

			dups = self.db.getOtherHashes(hexHash, self.archPath)

			# Short circuit on unique item, since we are only checking if ANY item is unique
			if not dups:
				return True

		return False

	def deleteArch(self):

		print("Would delete archive", self.archPath)
		return
		self.db.deleteBasePath(self.archPath)
		os.remove(self.archPath)


def go():


	checker = ArchChecker("/media/Storage/Manga/Tonari no Shugoshin [+~]/Tonari_no_Shugoshin_v2_ch5_[SnS].zip")
	checker.check()
	checker = ArchChecker("/media/Storage/Manga/Tonari no Shugoshin [+~]/Tonari_no_Shugoshin_v2_ch7_[EF].zip")
	checker.check()
	checker = ArchChecker("/media/Storage/Manga/Tonari no Shugoshin [+~]/Tonari_no_Shugoshin_v2_ch8_[EF].zip")
	checker.check()


if __name__ == "__main__":
	module = go()

