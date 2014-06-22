

import logSetup
logSetup.initLogging()

import nameTools as nt
import os.path
import os
import shutil

def deduplicateMangaFolders():
	pass
	dirDictDict = nt.dirNameProxy.getDirDicts()
	keys = list(dirDictDict.keys())
	keys.sort()

	for offset in range(len(keys)):
		curDict = dirDictDict[keys[offset]]
		curKeys = curDict.keys()
		for curKey in curKeys:
			for subKey in keys[offset+1:]:
				if curKey in dirDictDict[subKey]:
					print("Duplicate Directory", curKey)
					print("	", curDict[curKey])
					print("	", dirDictDict[subKey][curKey])

					fromDir = dirDictDict[subKey][curKey]
					toDir   = curDict[curKey]

					items = os.listdir(fromDir)
					for item in items:
						fromPath = os.path.join(fromDir, item)
						toPath   = os.path.join(toDir, item)

						if os.path.exists(toPath):
							raise ValueError("Duplicate file!")

						print("	Moving: ", item)
						print("	From: ", fromPath)
						print("	To:   ", toPath)
						shutil.move(fromPath, toPath)

def updateToMangaUpdatesNaming(dirTarget):
	pass


if __name__ == "__main__":
	try:
		deduplicateMangaFolders()
	finally:
		import nameTools as nt
		nt.dirNameProxy.stop()
