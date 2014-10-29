
from . import absImport
import settings
import UniversalArchiveReader
import os
import os.path
import logging
import rpyc



# Checks an archive (`archPath`) against the contents of the database
# accessible via the `settings.dedupApiFile` python file, which
# uses the absolute-import tool in the current directory.

# isBinaryUnique() returns True if the archive contains any unique items,
# false if it does not.

# isPhashUnique() returns True if the archive contains any phashes, False otherwise.
# The threhold for uniqueness is specified in PHASH_DISTANCE_THRESHOLD,
# which specifies the allowable hamming edit-distance between phash
# values that are still classified as identical. 1-3 are reasonable.
# 0 causes the call to behave very similarly to isBinaryUnique(),
# possibly allowing for extremely minor resave changes.

# deleteArch() deletes the archive which has path archPath,
# and also does the necessary database manipulation to reflect the fact that
# the archive has been deleted.


PHASH_DISTANCE_THRESHOLD = 3

def go():

	import logSetup
	logSetup.initLogging()


	remote = rpyc.connect("localhost", 12345)


	remote.root.loadTree('/media/Storage/MP')
	remote.root.loadTree('/media/Storage/H/MangaCMS')
	remote.root.loadTree('/media/Storage/Manga')

	checker = remote.root.ArchChecker("/media/Storage/MP/Nanatsu no Taizai [++++]/Nanatsu no Taizai - Chapter 96 - Chapter 96[MangaJoy].zip")
	print("Contains unique pHashes:", checker.isPhashUnique())
	print("Contains unique pHashes:", checker.isPhashUnique(5))
	print("Contains unique  hashes:", checker.isBinaryUnique())

	checker = remote.root.ArchChecker("/media/Storage/MP/Chaos;Head - Blue Complex [++];Chaos;Head - Blue Complex v01 c01.zip - Chaos;Head - Blue Complex v01 c01.zip")
	print("Contains unique pHashes:", checker.isPhashUnique())
	print("Contains unique  hashes:", checker.isBinaryUnique())
	# checker.addNewArch()


if __name__ == "__main__":
	go()

