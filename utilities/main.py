

print("Utilities Startup")
import runStatus
runStatus.preloadDicts = False

import logSetup
logSetup.initLogging()

import signal
import sys
import os.path
import utilities.dedupDir
import utilities.approxFileSorter
import utilities.autoOrganize as autOrg
import utilities.importer as autoImporter
import utilities.cleanDb
import utilities.bookClean
import utilities.cleanFiles
import deduplicator.remoteInterface

def printHelp():

	print("################################### ")
	print("##   System maintenance script   ## ")
	print("################################### ")
	print("")
	print("*********************************************************")
	print("Organizing Tools")
	print("*********************************************************")
	print("	import {dirPath}")
	print("		Import folders of manga from {dirPath}")
	print("		Assumes that {dirPath} is composed of directories containing manga")
	print("		zip files, and the directory is named after the series that it contains.")
	print()
	print("	organize {dirPath}")
	print("		Run auto-organizing tools against {dirPath}")
	print()
	print("	rename {dirPath}")
	print("		Rename directories in {dirPath} to match MangaUpdates naming")
	print()
	print("	dirs-clean {target-path} {del-dir}")
	print("		Find duplicates in each subdir of {target-path}, and remove them.")
	print("		Functions on a per-directory basis, so only duplicates in the same folder will be considered")
	print("		Does not currently use phashing.")
	print("		'Deleted' files are actually moved to {del-dir}, to allow checking before actual deletion.")
	print("		The moved files are named with the entire file-path, with the '/' being replaced with ';'.")
	print()
	print("	dir-clean {target-path} {del-dir}")
	print("		Find duplicates in {target-path}, and remove them.")
	print("		Functions on a per-directory basis, so only duplicates in the same folder will be considered")
	print("		Does not currently use phashing.")
	print("		'Deleted' files are actually moved to {del-dir}, to allow checking before actual deletion.")
	print("		The moved files are named with the entire file-path, with the '/' being replaced with ';'.")
	print("	")
	print("	dirs-restore {target-path}")
	print("		Reverses the action of 'dirs-clean'. {target-path} is the directory specified as ")
	print("		{del-dir} when running 'dirs-clean' ")
	print("	")
	print("	purge-dir {target-path}")
	print("		Processes the output of 'dirs-clean'. {target-path} is the directory specified as ")
	print("		{del-dir} when running 'dirs-clean'. ")
	print("		Each item in {del-dir} is re-confirmed to be a complete duplicate, and then truly deleted. ")
	print("	")
	print("	purge-dir-phash {target-path}")
	print("		Same as `purge-dir`, but uses phashes for duplicate detection as well.")
	print("	")
	print("	sort-dir-contents {target-path}")
	print("		Scan the contents of {target-path}, and try to infer the series for each file in said folders.")
	print("		If file doesn't match the series for the folder, and does match a known, valid folder, prompt")
	print("		to move to valid folder.")
	print("	")
	print("	move-unlinked {src-path} {to-path}")
	print("		Scan the contents of {src-path}, and try to infer the series for each subdirectory.")
	print("		If a subdir has no matching series, move it to {to-path}")
	print("	")
	print("	h-clean {del-dir}")
	print("		Walk through the historical H items and remove superceded duplicates.")
	print("		Processing is done in DB-ID order, which is roughtly chronological..")
	print("		'Deleted' files are actually moved to {del-dir}, to allow checking before actual deletion.")
	print("		The moved files are named with the entire file-path, with the '/' being replaced with ';'.")
	print("	")
	print("	src-clean {source-key} {del-dir}")
	print("		Find duplicates for all the items downloaded under the key {source-key}, and remove them.")
	print("		'Deleted' files are actually moved to {del-dir}, to allow checking before actual deletion.")
	print("		The moved files are named with the entire file-path, with the '/' being replaced with ';'.")

	print("*********************************************************")
	print("Miscellaneous Tools")
	print("*********************************************************")
	print("	lookup {name}")
	print("		Lookup {name} in the MangaUpdates name synonym lookup table, print the results.")
	print()
	print("	crosslink-books")
	print("		Make sure the netloc column of the book_items table is up to date.")
	print()
	print("	clean-book-cache")
	print("		Clean out and delete any old files from the book content cache")
	print("		that no longer has any entries in the database.")
	print()

	print("*********************************************************")
	print("Database Maintenance")
	print("*********************************************************")
	print("	reset-missing")
	print("		Reset downloads where the file is missing, and the download is not tagged as deduplicated.")
	print("	")
	print("	clear-bad-dedup")
	print("		Remove deduplicated tag from any files where the file exists.")
	print("	")
	print("	fix-bt-links")
	print("		Fix links for Batoto that point to batoto.com, rather then bato.to.")
	print("	")
	print("	cross-sync")
	print("		Sync name lookup table with seen series.")
	print("	")
	print("	update-bu-lut")
	print("		Regernate lookup strings for MangaUpdates table (needed if the `prepFilenameForMatching` call in nameTools is modified).")
	print("	")
	print("	fix-bad-series")
	print("		Consolidate series names to MangaUpdates standard naming.")
	print("	")
	print("	reload-tree")
	print("		Reload the BK tree from the database.")
	print("	")
	print("	lndb-cleaned-regen")
	print("		regenerate the set of cleaned LNDB item titles..")
	print("	")
	print("	truncate-trailing-novel")
	print("		Clean out the trailing '(Novel)' from mangaupdates novel items.")
	print("	")
	print("	fix-book-link-sources")
	print("		")
	print("	")
	print("	fix-bu-authors")
	print("		Fix authors from mangaupdates table where '[, Add, ]' got into the data due to incomplete parsing of the webpage")
	print("	")
	print("	fix-h-tags-case")
	print("		Fix issues where mixed-case H tags were being duplicated.")
	print("	")

	print("*********************************************************")
	print("Remote deduper interface")
	print("*********************************************************")
	print("phash-clean {targetDir} {removeDir}")
	print("		Find duplcates on the path {targetDir}, and move them to {removeDir}")
	print("		Duplicate search is done using the set of phashes contained within ")
	print("		{scanEnv}. ")
	print("		Requires deduper server interface to be running.")

	return


def parseOneArgCall(cmd):


	mainArg = sys.argv[1]

	print ("Passed arg", mainArg)


	pc = utilities.cleanDb.PathCleaner()
	pc.openDB()

	if mainArg.lower() == "reset-missing":
		pc.resetMissingDownloads()
	elif mainArg.lower() == "clear-bad-dedup":
		pc.clearInvalidDedupTags()
	elif mainArg.lower() == "fix-bt-links":
		pc.patchBatotoLinks()
	elif mainArg.lower() == "cross-sync":
		pc.crossSyncNames()
	elif mainArg.lower() == "update-bu-lut":
		pc.regenerateNameMappings()
	elif mainArg.lower() == "fix-bad-series":
		pc.consolidateSeriesNaming()
	elif mainArg.lower() == "fix-djm":
		pc.fixDjMItems()
	elif mainArg.lower() == "reload-tree":
		deduplicator.remoteInterface.treeReload()
	elif mainArg.lower() == "crosslink-books":
		utilities.bookClean.updateNetloc()
	elif mainArg.lower() == "clean-book-cache":
		utilities.bookClean.cleanBookContent()
	elif mainArg.lower() == "lndb-cleaned-regen":
		utilities.bookClean.regenLndbCleanedNames()
	elif mainArg.lower() == "truncate-trailing-novel":
		utilities.bookClean.truncateTrailingNovel()
	elif mainArg.lower() == "fix-book-link-sources":
		utilities.bookClean.fixBookLinkSources()
	elif mainArg.lower() == "fix-bu-authors":
		utilities.bookClean.fixMangaUpdatesAuthors()
	elif mainArg.lower() == "fix-h-tags-case":
		cleaner = utilities.cleanDb.HCleaner('None')
		cleaner.cleanTags()

	else:
		print("Unknown arg!")

	pc.closeDB()

def parseTwoArgCall(cmd, val):
	if cmd == "import":
		if not os.path.exists(val):
			print("Passed path '%s' does not exist!" % val)
			return
		autoImporter.importDirectories(val)
		return

	if cmd == "organize":
		if not os.path.exists(val):
			print("Passed path '%s' does not exist!" % val)
			return
		autOrg.organizeFolder(val)
		return

	elif cmd == "rename":
		if not os.path.exists(val):
			print("Passed path '%s' does not exist!" % val)
			return
		autOrg.renameSeriesToMatchMangaUpdates(val)
		return

	elif cmd == "lookup":
		print("Passed name = '%s'" % val)
		import nameTools as nt
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
	elif cmd == "purge-dir-phash":
		if not os.path.exists(val):
			print("Passed path '%s' does not exist!" % val)
			return
		utilities.dedupDir.purgeDedupTempsPhash(val)
		return

	elif cmd == "dirs-restore":
		if not os.path.exists(val):
			print("Passed path '%s' does not exist!" % val)
			return
		utilities.dedupDir.runRestoreDeduper(val)
		return

	elif cmd == "sort-dir-contents":
		if not os.path.exists(val):
			print("Passed path '%s' does not exist!" % val)
			return
		utilities.approxFileSorter.scanDirectories(val)
		return


	elif cmd == "clean-archives":
		if not os.path.exists(val):
			print("Passed path '%s' does not exist!" % val)
			return
		utilities.cleanFiles.cleanArchives(val)
		return

	elif cmd == "h-clean":
		if not os.path.exists(val):
			print("Passed path '%s' does not exist!" % val)
			return
		utilities.dedupDir.runHDeduper(val)
		return


	else:
		print("Did not understand command!")
		print("Sys.argv = ", sys.argv)

def parseThreeArgCall(cmd, arg1, arg2):
	if cmd == "dirs-clean":
		if not os.path.exists(arg1):
			print("Passed path '%s' does not exist!" % arg1)
			return
		elif not os.path.exists(arg2):
			print("Passed path '%s' does not exist!" % arg2)
			return
		utilities.dedupDir.runDeduper(arg1, arg2)
		return
	elif cmd == "src-clean":
		if not os.path.exists(arg2):
			print("Passed path '%s' does not exist!" % arg2)
			return
		utilities.dedupDir.runSrcDeduper(arg1, arg2)
		return
	elif cmd == "dir-clean":
		if not os.path.exists(arg1):
			print("Passed path '%s' does not exist!" % arg1)
			return
		if not os.path.exists(arg2):
			print("Passed path '%s' does not exist!" % arg2)
			return
		utilities.dedupDir.runSingleDirDeduper(arg1, arg2)
		return

	elif cmd == "move-unlinked":
		if not os.path.exists(arg1):
			print("Passed path '%s' does not exist!" % arg1)
			return
		if not os.path.exists(arg2):
			print("Passed path '%s' does not exist!" % arg2)
			return
		utilities.dedupDir.moveUnlinkable(arg1, arg2)
		return

	elif cmd == "auto-clean":
		if not os.path.exists(arg1):
			print("Passed path '%s' does not exist!" % arg1)
			return
		if not os.path.exists(arg2):
			print("Passed path '%s' does not exist!" % arg2)
			return
		deduplicator.remoteInterface.iterateClean(arg1, arg2)

	elif cmd == "h-fix":
		if not os.path.exists(arg2):
			print("Passed path '%s' does not exist!" % arg2)
			return

		cleaner = utilities.cleanDb.HCleaner(arg1)
		cleaner.resetMissingDownloads(arg2)
		return


	elif cmd == "phash-clean":
		if not os.path.exists(arg1):
			print("Passed path '%s' does not exist!" % arg1)
			return
		if not os.path.exists(arg2):
			print("Passed path '%s' does not exist!" % arg2)
			return
		deduplicator.remoteInterface.pClean(arg1, arg2)


	else:
		print("Did not understand command!")
		print("Sys.argv = ", sys.argv)

def parseFourArgCall(cmd, arg1, arg2, arg3):
	raise ValueError("Wat?")


def customHandler(dummy_signum, dummy_stackframe):
	if runStatus.run:
		runStatus.run = False
		print("Telling threads to stop")
	else:
		print("Multiple keyboard interrupts. Raising")
		raise KeyboardInterrupt


def parseCommandLine():
	signal.signal(signal.SIGINT, customHandler)
	if len(sys.argv) == 2:
		cmd = sys.argv[1].lower()
		parseOneArgCall(cmd)

	elif len(sys.argv) == 3:
		cmd = sys.argv[1].lower()
		val = sys.argv[2]
		parseTwoArgCall(cmd, val)

	elif len(sys.argv) == 4:

		cmd = sys.argv[1].lower()
		arg1 = sys.argv[2]
		arg2 = sys.argv[3]
		parseThreeArgCall(cmd, arg1, arg2)

	elif len(sys.argv) == 5:

		cmd = sys.argv[1].lower()
		arg1 = sys.argv[2]
		arg2 = sys.argv[3]
		arg3 = sys.argv[4]
		parseFourArgCall(cmd, arg1, arg2, arg3)

	else:
		printHelp()

if __name__ == "__main__":
	print("Command line parse")
	parseCommandLine()

