

import logSetup
logSetup.initLogging()

import nameTools as nt
import os.path
import os
import shutil
import settings
import ScrapePlugins.MonitorDbBase
import sys

import shutil


class dbInterface(ScrapePlugins.MonitorDbBase.MonitorDbBase):

	loggerPath       = "Main.Bu.Watcher"
	pluginName       = "BakaUpdates List Monitor"
	tableName        = "MangaSeries"
	nameMapTableName = "muNameList"

	dbName = settings.dbName

	def go(self):
		pass


def query_response(question):
	valid = {"f":"forward",
			 "r":"reverse",
			 "n":False}

	prompt = " [f/r/N] "

	while True:
		sys.stdout.write(question + prompt)
		choice = input().lower()
		if choice == '':
			return valid["n"]
		elif choice in valid:
			return valid[choice]
		else:
			sys.stdout.write("Invalid choice\n")


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
	idLut = nt.MtNamesMapWrapper()
	db = dbInterface()
	for key, luDict in nt.dirNameProxy.iteritems():
		mId = db.getIdFromDirName(key)

		# Skip cases where we have no match
		if not mId:
			continue

		dups = set()
		for name in idLut[mId]:
			cName = nt.prepFilenameForMatching(name)
			if cName in nt.dirNameProxy:
				dups.add(cName)
				db.getIdFromDirName(cName)
		if len(dups) > 1:
			row = db.getRowByValue(buId=mId)
			targetName = nt.prepFilenameForMatching(row["buName"])
			dest = nt.dirNameProxy[targetName]
			if luDict["dirKey"] != targetName and dest["fqPath"]:
				print("baseName = ", row["buName"], ", id = ", mId, ", names = ", dups)
				print(" Should move files from", luDict["fqPath"])
				print(" to directory          ", dest["fqPath"])
				doMove = query_response("move files?")
				if doMove == "forward":
					files = os.listdir(luDict["fqPath"])
					for fileN in files:
						fSrc = os.path.join(luDict["fqPath"], fileN)
						fDst = os.path.join(dest["fqPath"], fileN)
						print("		moving ", fSrc)
						print("		to     ", fDst)
						shutil.move(fSrc, fDst)
				elif doMove == "reverse":
					files = os.listdir(dest["fqPath"])
					for fileN in files:
						fSrc = os.path.join(dest["fqPath"], fileN)
						fDst = os.path.join(luDict["fqPath"], fileN)
						print("		moving ", fSrc)
						print("		to     ", fDst)
						shutil.move(fSrc, fDst)
		# row = db.getRowByValue(buId=mId)
		# fName = nt.prepFilenameForMatching(row["buName"])
		# if fName != key:
		# 	altNames = db.getNamesFromId(mId)

		# 	for name,  in altNames:
		# 		cName = nt.prepFilenameForMatching(name)
		# 		mId = db.getIdFromDirName(cName)

		# 		if cName != key and cName in nt.dirNameProxy:
		# 			print("Id = %s, '%s', '%s', '%s'" % (mId, key, fName, luDict["fqPath"]))
		# 			print("	altName = '%s'" % name)

if __name__ == "__main__":
	try:
		updateToMangaUpdatesNaming()
	finally:
		import nameTools as nt
		nt.dirNameProxy.stop()
