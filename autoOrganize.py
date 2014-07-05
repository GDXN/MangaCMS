

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

def query_response_bool(question):
	valid = {"y":True,
			 "n":False}

	prompt = " [y/N] "

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

def consolicateSeriesToSingleDir():
	print("Looking for series directories that can be flattened to a single dir")
	idLut = nt.MtNamesMapWrapper("buId->fsName")
	db = dbInterface()
	for key, luDict in nt.dirNameProxy.iteritems():
		# print("Key = ", key)
		mId = db.getIdFromDirName(key)

		# Skip cases where we have no match
		if not mId:
			continue

		dups = set()
		for name in idLut[mId]:
			cName = nt.prepFilenameForMatching(name)

			# Skip if it's one of the manga names that falls apart under the directory name cleaning mechanism
			if not cName:
				continue

			if cName in nt.dirNameProxy:
				dups.add(cName)
				db.getIdFromDirName(cName)
		if len(dups) > 1:
			row = db.getRowByValue(buId=mId)
			targetName = nt.prepFilenameForMatching(row["buName"])
			dest = nt.dirNameProxy[targetName]
			if luDict["dirKey"] != targetName and dest["fqPath"]:
				print("baseName = ", row["buName"], ", id = ", mId, ", names = ", dups)
				print(" Dir 1 ", luDict["fqPath"])
				print(" Dir 2 ", dest["fqPath"])
				doMove = query_response("move files ('f' dir 1 -> dir 2. 'r' dir 2 -> dir 1. 'n' do not move)?")
				if doMove == "forward":
					moveFiles(luDict["fqPath"], dest["fqPath"])
					os.rmdir(luDict["fqPath"])
				elif doMove == "reverse":
					moveFiles(dest["fqPath"], luDict["fqPath"])
					os.rmdir(dest["fqPath"])


def moveFiles(srcDir, dstDir):

	files = os.listdir(srcDir)
	for fileN in files:
		fSrc = os.path.join(srcDir, fileN)
		fDst = os.path.join(dstDir, fileN)
		print("		moving ", fSrc)
		print("		to     ", fDst)
		shutil.move(fSrc, fDst)

def renameSeriesToMatchMangaUpdates(scanpath):
	idLut = nt.MtNamesMapWrapper("fsName->buId")
	muLut = nt.MtNamesMapWrapper("buId->buName")
	db = dbInterface()
	print("Scanning")
	foundDirs = 0
	contents = os.listdir(scanpath)
	for dirName in contents:
		cName = nt.prepFilenameForMatching(dirName)
		mtId = idLut[cName]
		if mtId and len(mtId) > 1:
			print("Multiple mtId values for '%s' ('%s')" % (cName, dirName))
			print("	", mtId)
			print("	Skipping item")

		elif mtId:
			mtId = mtId.pop()
			mtName = muLut[mtId].pop()
			cMtName = nt.prepFilenameForMatching(mtName)
			if cMtName != cName:
				print("Dir '%s' ('%s')" % (cName, dirName))
				print("	Should be '%s'" % (mtName, ))
				print("	URL: https://www.mangaupdates.com/series.html?id=%s" % (mtId, ))
				oldPath = os.path.join(scanpath, dirName)
				newPath = os.path.join(scanpath, nt.makeFilenameSafe(mtName))
				if not os.path.isdir(oldPath):
					raise ValueError("Not a dir. Wat?")



				print("	old '%s'" % (oldPath, ))
				print("	new '%s'" % (newPath, ))

				newCl = nt.cleanUnicode(newPath)
				if newCl != newPath:
					print("Unicode oddness. Skipping")
					continue

				rating = nt.extractRatingToInt(oldPath)

				if rating != 0:
					print("	Need to add rating = ", rating)

				mv = query_response_bool("	rename?")

				if mv:

					#
					if os.path.exists(newPath):
						print("Target dir exists! Moving files instead")
						moveFiles(oldPath, newPath)
						os.rmdir(oldPath)
						nt.dirNameProxy.changeRatingPath(newPath, rating)
					else:
						os.rename(oldPath, newPath)
						nt.dirNameProxy.changeRatingPath(newPath, rating)
			foundDirs += 1

	print("Total directories that need renaming", foundDirs)
	#	for key, luDict in nt.dirNameProxy.iteritems():
	# 	mId = db.getIdFromDirName(key)

	# 	Skip cases where we have no match
	# 	if not mId:
	# 		continue

	# 	dups = set()
	# 	muNames = idLut[mId]
	# 	print("Names", muNames)
	# print("All items:")
	# for key, val in idLut.iteritems():
	# 	print("key, val:", key, val)
	# print("exiting")

if __name__ == "__main__":
	try:
		deduplicateMangaFolders()
		consolicateSeriesToSingleDir()
		renameSeriesToMatchMangaUpdates("/media/Storage/Manga")
	finally:
		nt.dirNameProxy.stop()
