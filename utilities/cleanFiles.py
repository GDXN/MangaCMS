# import sys
# sys.path.insert(0,"..")
import os.path
import os
import logSetup
if __name__ == "__main__":
	logSetup.initLogging()

import UniversalArchiveInterface
import traceback

import runStatus
runStatus.preloadDicts = False

import archCleaner

def cleanArchives(baseDir):
	print(baseDir)
	cleaner = archCleaner.ArchCleaner()

	for root, dirs, files in os.walk(baseDir):
		for name in files:
			fileP = os.path.join(root, name)
			print("Processing", fileP)

			try:
				if UniversalArchiveInterface.ArchiveReader.isArchive(fileP):
					cleaner.cleanZip(fileP)

			except:
				print("ERROR")
				traceback.print_exc()
				pass