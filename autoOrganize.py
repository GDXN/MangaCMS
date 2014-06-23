

import logSetup
logSetup.initLogging()

import nameTools as nt
import os.path
import os
import shutil
import settings
import ScrapePlugins.MonitorDbBase

class dbInterface(ScrapePlugins.MonitorDbBase.MonitorDbBase):

	loggerPath       = "Main.Bu.Watcher"
	pluginName       = "BakaUpdates List Monitor"
	tableName        = "MangaSeries"
	nameMapTableName = "muNameList"

	dbName = settings.dbName

	def go(self):
		pass

# Removes duplicate manga directories from the various paths specified in
# settings.py. Basically, if you have a duplicate of a folder name, it moves the
# files from the directory with a larger index key to the smaller index key
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

def updateToMangaUpdatesNaming():
	db = dbInterface()
	for key, luDict in nt.dirNameProxy.iteritems():
		mId = db.getIdFromName(key)

		# Skip cases where we have no match
		if not mId:
			continue

		row = db.getRowByValue(buId=mId)
		fName = nt.prepFilenameForMatching(row["buName"])
		if fName != key:
			altNames = db.getNamesFromId(mId)

			for name,  in altNames:
				mId = db.getIdFromName(name)
				cName = nt.prepFilenameForMatching(name)

				if cName != key and cName in nt.dirNameProxy:
					print("Id = %s, '%s', '%s', '%s'" % (mId, key, fName, luDict["fqPath"]))
					print("	altName = '%s'" % name)

if __name__ == "__main__":
	try:
		updateToMangaUpdatesNaming()
	finally:
		import nameTools as nt
		nt.dirNameProxy.stop()
