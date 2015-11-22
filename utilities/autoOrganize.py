
# Yes, this whole file is kind of a mish-mash of random
# script segments.

import nameTools as nt
import os.path
import os
import shutil
import settings
import ScrapePlugins.MonitorDbBase


import psycopg2
import Levenshtein as lv

from utilities.cleanDb import PathCleaner


from utilities.askUser import query_response, query_response_bool

# from deduplicator.DbUtilities import DedupManager


class DbInterface(ScrapePlugins.MonitorDbBase.MonitorDbBase):

	loggerPath       = "Main.Org.Tool"
	pluginName       = "Organization Tool"
	tableName        = "MangaSeries"
	nameMapTableName = "muNameList"
	changedTableName = "muItemChanged"
	itemReleases     = "muReleases"

	dbName = settings.DATABASE_DB_NAME

	def go(self):
		pass




# Removes duplicate manga directories from the various paths specified in
# settings.py. Basically, if you have a duplicate of a folder name, it moves the
# files from the directory with a larger index key to the smaller index key
def consolidateMangaFolders(dirPath, smartMode=True):


	idLut = nt.MtNamesMapWrapper("fsName->buId")

	pc = PathCleaner()
	pc.openDB()



	count = 0
	print("Dir", dirPath)
	items = os.listdir(dirPath)
	items.sort()
	for item in items:
		item = os.path.join(dirPath, item)
		if os.path.isdir(item):
			fPath, dirName = os.path.split(item)

			lookup = nt.dirNameProxy[dirName]
			if lookup["fqPath"] != item:
				print()
				print()
				print("------------------------------------------------------")
				canonName = nt.getCanonicalMangaUpdatesName(dirName)
				print("Duplicate Directory '%s' - Canon = '%s'" % (dirName, canonName))

				count += 1

				mtId = idLut[nt.prepFilenameForMatching(dirName)]
				for num in mtId:
					print("	URL: https://www.mangaupdates.com/series.html?id=%s" % (num, ))

				fPath, dir2Name = os.path.split(lookup["fqPath"])


				if not os.path.exists(item):
					print("'%s' has been removed. Skipping" % item)
					continue
				if not os.path.exists(lookup["fqPath"]):
					print("'%s' has been removed. Skipping" % lookup["fqPath"])
					continue


				n1 = lv.distance(dirName, canonName)
				n2 = lv.distance(dir2Name, canonName)

				r1 = abs(nt.extractRatingToFloat(dirName))
				r2 = abs(nt.extractRatingToFloat(dir2Name))

				if "[complete]" in dirName.lower():
					r1 += 0.1
				if "[complete]" in dir2Name.lower():
					r2 += 0.1

				if "[wtf]" in dirName.lower():
					r1 += 0.2
				if "[wtf]" in dir2Name.lower():
					r2 += 0.2


				print("	1: ", item)
				print("	2: ", lookup["fqPath"])
				print("	1:	", dirName, ' ->', nt.getCanonicalMangaUpdatesName(dirName))
				print("	2:	", dir2Name, ' ->', nt.getCanonicalMangaUpdatesName(dir2Name))
				print("	1:	({num} items)(distance {dist})(rating {rat})".format(num=len(os.listdir(item)), dist=n1, rat=r1))
				print("	2:	({num} items)(distance {dist})(rating {rat})".format(num=len(os.listdir(lookup["fqPath"])), dist=n2, rat=r2))



				mtId2 = idLut[nt.prepFilenameForMatching(dir2Name)]
				if mtId != mtId2:
					print("DISCORDANT ID NUMBERS - {num1}, {num2}!".format(num1=mtId, num2=mtId2))
					for num in mtId2:
						print("	URL: https://www.mangaupdates.com/series.html?id=%s" % (num, ))

					continue

				if r1 > r2:
					doMove = "reverse"
				elif r2 > r1:
					doMove = "forward"
				else:
					doMove = ''

				if not doMove or not smartMode:
					doMove = query_response("move files ('f' dir 1 -> dir 2. 'r' dir 1 <- dir 2. 'l' use levenshtein distance. 'n' do not move)?")

				if doMove == "forward":
					print("Forward move")
					fromDir = item
					toDir   = lookup["fqPath"]
				elif doMove == "reverse":
					print("Reverse move")
					fromDir = lookup["fqPath"]
					toDir   = item
				elif doMove == "levenshtein":
					print("Levenshtein distance chooser")


					# I'm using less then or equal, so situations where
					# both names are equadistant get aggregated anyways.
					if n1 <= n2:
						fromDir = lookup["fqPath"]
						toDir   = item
					else:
						fromDir = item
						toDir   = lookup["fqPath"]

				else:
					print("Skipping")
					continue

				print("moving from: '%s' " % fromDir)
				print("         to: '%s' " % toDir)



				items = os.listdir(fromDir)
				for item in items:
					fromPath = os.path.join(fromDir, item)
					toPath   = os.path.join(toDir, item)

					loop = 2
					while os.path.exists(toPath):
						pathBase, ext = os.path.splitext(toPath)
						print("	Duplicate file!")
						toPath = "{start} ({loop}){ext}".format(start=pathBase, loop=loop, ext=ext)
					print("		Moving: ", item)
					print("		From: ", fromPath)
					print("		To:   ", toPath)
					pc.moveFile(fromPath, toPath)

					try:
						pc.moveFile(fromPath, toPath)
					except psycopg2.IntegrityError:
						print("Error moving item in dedup database")

						# pc.deletePath(toPath)

					shutil.move(fromPath, toPath)


				print("Deleting directory")
				os.rmdir(fromDir)

	print("total items", count)
# Removes duplicate manga directories from the various paths specified in
# settings.py. Basically, if you have a duplicate of a folder name, it moves the
# files from the directory with a larger index key to the smaller index key
def deduplicateMangaFolders():

	dirDictDict = nt.dirNameProxy.getDirDicts()
	keys = list(dirDictDict.keys())
	keys.sort()

	pc = PathCleaner()
	pc.openDB()
	# dm = DedupManager()


	for offset in range(len(keys)):
		curDict = dirDictDict[keys[offset]]
		curKeys = curDict.keys()
		for curKey in curKeys:
			if not curKey:
				print("Invalid key!", curKey)
				continue
			for subKey in keys[offset+1:]:
				if curKey in dirDictDict[subKey]:
					print("Duplicate Directory for key '%s'" % curKey)
					print("	Preferred:", curDict[curKey])
					print("	Duplicate:", dirDictDict[subKey][curKey])



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
						print("Moving: ", item)
						print("	From: ", fromPath)
						print("	To:   ", toPath)
						pc.moveFile(fromPath, toPath)

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

				print("	URL: https://www.mangaupdates.com/series.html?id=%s" % (mId, ))
				print(" Dir 1 ", luDict["fqPath"])
				print(" Dir 2 ", dest["fqPath"])

				dirName = os.path.split(luDict["fqPath"])[-1]
				dir2Name = os.path.split(dest["fqPath"])[-1]

				print("	1:	", dirName, ' ->', nt.getCanonicalMangaUpdatesName(dirName))
				print("	2:	", dir2Name, ' ->', nt.getCanonicalMangaUpdatesName(dir2Name))
				print("	1:	({num} items)".format(num=len(os.listdir(luDict["fqPath"]))))
				print("	2:	({num} items)".format(num=len(os.listdir(dest["fqPath"]))))


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

				rating = nt.extractRatingToFloat(oldPath)

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


def organizeFolder(folderPath):
	try:
		nt.dirNameProxy.startDirObservers(useObservers=False)
		consolidateMangaFolders(folderPath)
		deduplicateMangaFolders()
		consolicateSeriesToSingleDir()

	finally:
		try:
			nt.dirNameProxy.stop()
		except:
			print("Observer not running?")

