
# Yes, this whole file is kind of a mish-mash of random
# script segments.

import runStatus
runStatus.preloadDicts = False


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

from utilities.cleanDb import PathCleaner
import utilities.dedupDir

from deduplicator.DbUtilities import DedupManager

class DbInterface(ScrapePlugins.MonitorDbBase.MonitorDbBase):

	loggerPath       = "Main.Org.Tool"
	pluginName       = "Organization Tool"
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

	dirDictDict = nt.dirNameProxy.getDirDicts()
	keys = list(dirDictDict.keys())
	keys.sort()

	pc = PathCleaner()
	pc.openDB()
	dm = DedupManager()


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

						loop = 2
						while os.path.exists(toPath):
							pathBase, ext = os.path.splitext(toPath)
							print("Duplicate file!")
							toPath = "{start} ({loop}){ext}".format(start=pathBase, loop=loop, ext=ext)
						print("	Moving: ", item)
						print("	From: ", fromPath)
						print("	To:   ", toPath)
						pc.moveFile(fromPath, toPath)
						dm.moveFile(fromPath, toPath)
						shutil.move(fromPath, toPath)

def consolicateSeriesToSingleDir():
	print("Looking for series directories that can be flattened to a single dir")
	idLut = nt.MtNamesMapWrapper("buId->fsName")
	db = DbInterface()
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
	db = DbInterface()
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


def testDelete():
	db = DbInterface()
	cur = db.conn.cursor()
	cur.execute("INSERT INTO munamelist (buId, name) VALUES ('1000', 'LOLERCOASTER');")
	cur.execute("DELETE FROM munamelist WHERE name='LOLERCOASTER'")
	print("Results = ", cur.rowcount)

def organizeFolder(folderPath):
	try:
		nt.dirNameProxy.startDirObservers()
		deduplicateMangaFolders()
		consolicateSeriesToSingleDir()

	finally:
		nt.dirNameProxy.stop()

def printHelp():
	print("Valid arguments:")
	print("	python3 autoOrganize organize {dirPath}")
	print("		Run auto-organizing tools against {dirPath}")
	print()
	print("	python3 autoOrganize rename {dirPath}")
	print("		Rename directories in {dirPath} to match MangaUpdates naming")
	print()
	print("	python3 autoOrganize lookup {name}")
	print("		Lookup {name} in the MangaUpdates name synonym lookup table, print the results.")
	print()
	print("	python3 autoOrganize dirs-clean {target-path} {del-dir}")
	print("		Find duplicates in each subdir of {target-path}, and remove them.")
	print("		Functions on a per-directory basis, so only duplicates in the same folder will be considered")
	print("		Does not currently use phashing.")
	print("		'Deleted' files are actually moved to {del-dir}, to allow checking before actual deletion.")
	print("		The moved files are named with the entire file-path, with the '/' being replaced with ';'.")
	print()
	print("	python3 autoOrganize dir-clean {target-path} {del-dir}")
	print("		Find duplicates in {target-path}, and remove them.")
	print("		Functions on a per-directory basis, so only duplicates in the same folder will be considered")
	print("		Does not currently use phashing.")
	print("		'Deleted' files are actually moved to {del-dir}, to allow checking before actual deletion.")
	print("		The moved files are named with the entire file-path, with the '/' being replaced with ';'.")
	print("	")
	print("	python3 autoOrganize dirs-restore {target-path}")
	print("		Reverses the action of 'dirs-clean'. {target-path} is the directory specified as ")
	print("		{del-dir} when running 'dirs-clean' ")
	print("	")
	print("	python3 autoOrganize purge-dir {target-path}")
	print("		Processes the output of 'dirs-clean'. {target-path} is the directory specified as ")
	print("		{del-dir} when running 'dirs-clean'. ")
	print("		Each item in {del-dir} is re-confirmed to be a complete duplicate, and then truly deleted. ")
	print("	")

def parseCommandLine():
	if len(sys.argv) == 3:
		cmd = sys.argv[1].lower()
		val = sys.argv[2]

		if cmd == "organize":
			if not os.path.exists(val):
				print("Passed path '%s' does not exist!" % val)
				return
			organizeFolder(val)
			return

		elif cmd == "rename":
			if not os.path.exists(val):
				print("Passed path '%s' does not exist!" % val)
				return
			renameSeriesToMatchMangaUpdates(val)
			return

		elif cmd == "lookup":
			print("Passed name = '%s'" % val)
			haveLookup = nt.haveCanonicalMangaUpdatesName(val)
			if not haveLookup:
				print("Item not found in MangaUpdates name synonym table")
				print("Processed item as searched = '%s'" % nt.prepFilenameForMatching(val))
			else:
				print("Item found in lookup table!")
				print("Canonical name = '%s'" % nt.getCanonicalMangaUpdatesName(val) )


		elif cmd == "purge-dir":
			if not os.path.exists(val):
				print("Passed path '%s' does not exist!" % val)
				return
			utilities.dedupDir.purgeDedupTemps(val)
			return

		elif cmd == "dirs-restore":
			if not os.path.exists(val):
				print("Passed path '%s' does not exist!" % val)
				return
			utilities.dedupDir.runRestoreDeduper(val)
			return


		else:
			print("Did not understand command!")
			print("Sys.argv = ", sys.argv)


	elif len(sys.argv) == 4:

		cmd = sys.argv[1].lower()
		arg1 = sys.argv[2]
		arg2 = sys.argv[3]

		if cmd == "dirs-clean":
			if not os.path.exists(arg1) or not os.path.exists(arg2):
				print("Passed path '%s' does not exist!" % val)
				return
			if not os.path.exists(arg2):
				print("Passed path '%s' does not exist!" % arg2)
				return
			utilities.dedupDir.runDeduper(arg1, arg2)
			return
		if cmd == "dir-clean":
			if not os.path.exists(arg1):
				print("Passed path '%s' does not exist!" % arg1)
				return
			if not os.path.exists(arg2):
				print("Passed path '%s' does not exist!" % arg2)
				return
			utilities.dedupDir.runSingleDirDeduper(arg1, arg2)
			return

		else:
			print("Did not understand command!")
			print("Sys.argv = ", sys.argv)
	elif len(sys.argv) == 2:
		cmd = sys.argv[1].lower()
		if cmd == "test":
			testDelete()
			return
	else:
		printHelp()


if __name__ == "__main__":
	parseCommandLine()
