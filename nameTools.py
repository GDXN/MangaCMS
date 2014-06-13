

import re

import settings
import logging
import sqlite3
import time
import logSetup
import threading
import os
import os.path

import unicodedata

import pyinotify

# --------------------------------------------------------------

def prepFilenameForMatching(inStr):
	inStr = sanitizeString(inStr)
	inStr = makeFilenameSafe(inStr)
	return inStr

def makeFilenameSafe(inStr):
	inStr = inStr.replace("%20", " ") \
				 .replace("<",  "") \
				 .replace(">",  "") \
				 .replace(":",  "") \
				 .replace("\"", "") \
				 .replace("/",  "") \
				 .replace("\\", "") \
				 .replace("|",  "") \
				 .replace("?",  "") \
				 .replace("*",  "") \
				 .replace('"', "")

	inStr = inStr.rstrip(".")  # Windows file names can't end in dot. For some reason.
	inStr = inStr.rstrip(" ")  # And can't have leading or trailing spaces
	inStr = inStr.lstrip(" ")

	return inStr


def cleanName(inStr):
	cleanedName = sanitizeString(inStr)
	cleanedName = unicodedata.normalize("NFKD", cleanedName).encode("ascii", errors="ignore").decode()
	return cleanedName

bracketStripRe = re.compile(r"(\[[\+\~\-\!\d\w:]*\])")

# Basically used for dir-path cleaning to prep for matching, and not much else
def sanitizeString(inStr, flatten=True):

	if inStr in nameLookup:
		inStr = nameLookup[inStr]


	baseName = bracketStripRe.sub(" ", inStr)				#clean brackets

	if baseName in nameLookup:
		baseName = nameLookup[baseName]
	if flatten:
		baseName = baseName.replace("~", "")		 # Spot fixes. We'll see if they break anything
		baseName = baseName.replace(".", "")
		baseName = baseName.replace(";", "")
		baseName = baseName.replace(":", "")
		baseName = baseName.replace("-", "")
		baseName = baseName.replace("?", "")
		baseName = baseName.replace("!", "")
		baseName = baseName.replace('"', "")

	# baseName = baseName.replace("'", "")
	baseName = baseName.replace("  ", " ")

	# baseName = unicodedata.normalize('NFKD', baseName).encode("ascii", errors="ignore")  # This will probably break shit


	return baseName.lower().rstrip().lstrip()

def extractRating(inStr):
	search = re.search(r"^(.*?)\[([~+\-!]+)\](.*?)$", inStr)
	if search:
		# print("Found rating! Prefix = {pre}, rating = {rat}, postfix = {pos}".format(pre=search.group(1), rat=search.group(2), pos=search.group(3)))
		return search.group(1), search.group(2), search.group(3)
	else:
		return inStr, "", ""



def getCleanedName(inStr):
	inStr = re.sub(r"\d+\-\d+",                " ", inStr)				#Scrub interdigit hyphens
	inStr = re.sub(r"([\[\]_\+0-9()=,\?])",    " ", inStr)				#clean brackets, symbols, and numbers: (Removed "-")
	inStr = re.sub(r"\W(ch|vol)[0-9]+?",       " ", inStr)				#Clean 'ch01' or similar
	inStr = re.sub(r"\W[vc][0-9]*?\W",         " ", inStr)				#Clean 'v01' and 'c01' or similar
	inStr = re.sub(r"\W[a-zA-z0-9]\W",         " ", inStr)				#Remove all single letters
	inStr = re.sub(r"\W[lL][Qq]\W",            " ", inStr)				#Remove "[LQ]"
	inStr = re.sub(r" +",                      " ", inStr)				#Collapse spaces

	inStr = inStr.rstrip().lstrip()
	return inStr






def isProbablyImage(fileName):
	imageExtensions = [".jpeg", ".jpg", ".gif", ".png", ".apng", ".svg", ".bmp"]
	fileName = fileName.lower()
	for ext in imageExtensions:
		if fileName.endswith(ext):
			return True

	return False






# ------------------------------------------------------


# Caching proxy that makes a DB look like a dict, and at the same time rate-limits the DB update queries, for when look-ups are done in a iterative loop
# Opens a dynamically specifiable database, though the database must be one of a predefined set.
class MapWrapper(object):

	# Make it a borg class (all instances share state)
	_shared_state = {}

	log = logging.getLogger("Main.NSLookup")

	dbPath = settings.dbName

	validTables = {
		"mangaNameMappings"  : ["mangaNameMappings",  "(mangaUpdates text NOT NULL, mangaTraders text NOT NULL, PRIMARY KEY(mangaTraders) ON CONFLICT REPLACE)"],
		"folderNameMappings" : ["folderNameMappings", "(baseName text NOT NULL, folderName text NOT NULL, PRIMARY KEY(baseName, folderName) ON CONFLICT REPLACE)"]

	}

	def __init__(self, tableName):
		self.__dict__ = self._shared_state

		self.updateLock = threading.Lock()

		if not tableName in self.validTables:
			raise ValueError("Invalid table name specified!")

		self.log.info("Loading NSLookup")
		self.tableName = self.validTables[tableName][0]
		self.tableSchema = self.validTables[tableName][1]
		self.openDB()

		self.lastUpdate = 0
		self.items = {}
		self.updateFromDB()

	def stop(self):
		self.log.info("Unoading NSLookup")
		self.closeDB()

	def openDB(self):
		self.log.info( "NSLookup Opening DB...",)
		self.conn = sqlite3.connect(self.dbPath, timeout=30, check_same_thread=False)
		self.log.info("opened")
		cur = self.conn.cursor()
		ret = cur.execute('''SELECT name FROM sqlite_master WHERE type='table' AND name='%s';''' % self.tableName)
		rets = ret.fetchall()
		if rets:
			rets = rets[0]
		if not self.tableName in rets:   # If the DB doesn't exist, set it up.
			self.log.info("DB Not setup for %s. Creating table", self.tableName)
			self.conn.execute('''CREATE TABLE %s %s''' % (self.tableName, self.tableSchema))
			# raise ValueError("%s Database does not exist. Name mapper cannot work." % self.tableName)

		self.log.info("Activating 'wal' mode")
		rets = self.conn.execute('''PRAGMA journal_mode=wal;''')
		rets = rets.fetchall()

		self.log.info("PRAGMA return value = %s", rets)

	def closeDB(self):
		self.log.info( "Closing DB...")
		self.conn.close()
		self.log.info( "done")

	def updateFromDB(self, force=False):
		# Only query the database at most once per 5 seconds.
		if time.time() > self.lastUpdate + 5 or force:
			self.updateLock.acquire()
			self.log.info("NSLookupTool updating from DB. Self - %s", self)
			cur = self.conn.cursor()
			cur.execute('SELECT * FROM %s;' % self.tableName)
			rets = cur.fetchall()

			temp = {}

			for muName, mtName in rets:
				temp[muName] = mtName

			self.items = temp
			self.lastUpdate = time.time()


			self.updateLock.release()

	def iteritems(self):
		self.updateFromDB()

		keys = list(self.items.keys())  # I want the items sorted by name, so we have to sort the list of keys, and then iterate over that.
		keys.sort()

		for key in keys:
			yield key, self.items[key]


	def __getitem__(self, key):
		self.updateFromDB()
		return self.items[key]

	def __contains__(self, key):
		self.updateFromDB()
		return key in self.items




class EventHandler(pyinotify.ProcessEvent):
	def __init__(self, paths):
		super(pyinotify.ProcessEvent, self).__init__()
		self.paths = {}
		for path in paths:
			self.paths[path] = False
		self.updateLock = threading.Lock()

	def process_default(self, event):
		self.updateLock.acquire()
		# print("Dir monitor detected change!", event)
		for path in self.paths.keys():
			if event.path.startswith(path):
				self.paths[path] |= True
				# print("Changed base-path = ", path)
		# print("Event path?", event.path)
		self.updateLock.release()

	def setPathDirty(self, path):
		print("Setting path '{path}' as dirty".format(path=path))
		self.updateLock.acquire()
		self.paths[path] = True
		self.updateLock.release()

	def getClearChangedStatus(self, path):

		self.updateLock.acquire()
		ret = self.paths[path]
		self.paths[path] = False
		self.updateLock.release()

		return ret


MONITORED_FS_EVENTS = pyinotify.IN_CREATE | pyinotify.IN_DELETE | pyinotify.IN_MODIFY | pyinotify.IN_MOVED_FROM | \
						pyinotify.IN_MOVED_TO | pyinotify.IN_MOVE_SELF | pyinotify.IN_MODIFY | pyinotify.IN_ATTRIB

# Caching proxy that makes a directories look like a dict.
# Does folder-name mangling to provide case-insensitivity, and provide some
# robusness to minor name variations.
class DirNameProxy(object):

	# Make it a borg class (all instances share state)
	_shared_state = {}


	log = logging.getLogger("Main.DirLookup")


	def __init__(self, paths):
		self.__dict__ = self._shared_state

		self.updateLock = threading.Lock()


		self.paths = paths
		if not "wm" in self.__dict__:
			self.wm = pyinotify.WatchManager()
			self.eventH = EventHandler([item["dir"] for item in self.paths.values()])
			self.notifier = pyinotify.ThreadedNotifier(self.wm, self.eventH)

		self.log.info("Setting up filesystem observers")
		for key in self.paths.keys():
			if not "observer" in self.paths[key]:
				self.log.info("Instantiating observer for path %s" % self.paths[key]["dir"])

				self.paths[key]["observer"] = self.wm.add_watch(self.paths[key]["dir"], MONITORED_FS_EVENTS, rec=True)


			else:
				self.log.info("WARNING = DirNameProxy Instantiated multiple times!")

		self.notifier.start()
		self.log.info("Filesystem observers initialized")
		self.log.info("Loading DirLookup")

		self.lastCheck = 0
		self.maxRate = 5
		self.dirDicts = {}
		self.checkUpdate(force=True)
		baseDictKeys = list(self.dirDicts.keys())
		baseDictKeys.sort()

		# for watch in self.

	def stop(self):

		self.log.info("Unoading DirLookup")
		self.notifier.stop()

	def getDirDict(self, dlPath):

		self.log.info( "Loading Output Dirs for path '%s'...", dlPath)

		targetContents = os.listdir(dlPath)
		targetContents.sort()
		#self.log.info( "targetContents", targetContents)
		targets = {}
		for dirPath in targetContents:
			fullPath = os.path.join(dlPath, dirPath)
			if os.path.isdir(fullPath):
				baseName = prepFilenameForMatching(dirPath)
				# baseName = makeFilenameSafe(dirPath)
				# self.log.info("%s is a dir %s Basepath %s", dirPath, fullPath, baseName)
				# self.log.info( "RawName = ", baseName)
				targets[baseName] = fullPath
		self.log.info( "Done")


		return targets


	def checkUpdate(self, force=False, skipTime=False):

		updateTime = time.time()
		if not updateTime > (self.lastCheck + self.maxRate) and (not force) and (not skipTime):
			print("DirDicts not stale!")
			return
		self.updateLock.acquire()

		self.lastCheck = updateTime

		keys = list(self.paths.keys())
		keys.sort()
		# print("Keys = ", keys)
		# print("DirNameLookup checking for changes (force=%s)!" % force)

		for key in keys:
			# Only query the filesystem at most once per *n* seconds.
			if updateTime > self.paths[key]["lastScan"] + self.paths[key]["interval"] or force or skipTime:
				changed = self.eventH.getClearChangedStatus( self.paths[key]["dir"])

				if changed or force:
					self.log.info("DirLookupTool updating %s, path=%s!", key, self.paths[key]["dir"])
					self.log.info("DirLookupTool updating from Directory")
					self.dirDicts[key] = self.getDirDict(self.paths[key]["dir"])
					self.paths[key]["lastScan"] = updateTime

		self.updateLock.release()

	def changeRating(self, mangaName, newRating):
		item = self[mangaName]
		if not item['fqPath']:
			raise ValueError("Invalid item")

		print("Item", item)
		print("Path", self.paths[item['sourceDict']]['dir'])

		oldPath = item['fqPath']
		prefix, dummy_rating, postfix = extractRating(oldPath)

		print("Rating change call!")
		if newRating > 0 and newRating <= 5:
			ratingStr = "+"*newRating
		elif newRating == 0:
			ratingStr = ""
		elif newRating == -1:
			ratingStr = "-"
		else:
			raise ValueError("Invalid rating value!")

		if len(ratingStr):
			ratingStr = " [{rat}] ".format(rat=ratingStr)

		newPath = "{pre}{rat}{pos}".format(pre=prefix, rat=ratingStr, pos=postfix)
		newPath = newPath.rstrip(" ").lstrip(" ")

		print("Oldpath = ", oldPath)
		print("Newpath = ", newPath)
		if oldPath != newPath:
			if os.path.exists(newPath):
				raise ValueError("New path exists already!")
			else:
				os.rename(oldPath, newPath)
				self.eventH.setPathDirty(self.paths[item['sourceDict']]['dir'])
				print("Calling checkUpdate")
				self.checkUpdate(skipTime=True)
				print("checkUpdate Complete")


	def filterNameThroughDB(self, name):
		if name in dirsLookup:
			return dirsLookup[name]
		else:
			return name

	def getUnsanitizedName(self, name):
		name = self.filterNameThroughDB(name)
		return self[name]

	def getPathByKey(self, key):
		return self.paths[key]

	def getDirDicts(self):
		return self.dirDicts

	def getRawDirDict(self, key):
		return self.dirDicts[key]

	def getFromSpecificDict(self, dictKey, itemKey):
		filteredKey = self.filterNameThroughDB(itemKey)
		if filteredKey in self.dirDicts[dictKey]:
			tmp = self.dirDicts[dictKey][filteredKey]
			return self._processItemIntoRet(tmp, itemKey, filteredKey, dictKey)

		return {"fqPath" : None, "item": None, "inKey" : None, "dirKey": None, "rating": None, "sourceDict": None}



	def whichDictContainsKey(self, itemKey):
		baseDictKeys = list(self.dirDicts.keys())
		baseDictKeys.sort()
		for dirDictKey in baseDictKeys:
			if itemKey in self.dirDicts[dirDictKey]:
				return dirDictKey
		return False

	def iteritems(self):
		# self.checkUpdate()

		baseDictKeys = list(self.dirDicts.keys())
		baseDictKeys.sort()
		for dirDictKey in baseDictKeys:
			keys = list(self.dirDicts[dirDictKey].keys())  # I want the items sorted by name, so we have to sort the list of keys, and then iterate over that.
			keys.sort()

			for key in keys:
				yield key, self[key]

	def _processItemIntoRet(self, item, origKey, filteredKey, dirDictKey):
		dummy_basePath, dirName = os.path.split(item)
		dummy_prefix, rating, dummy_postfix = extractRating(dirName)
		ret = {"fqPath" : item, "item": dirName, "inKey" : origKey, "dirKey": filteredKey, "rating": rating, "sourceDict": dirDictKey}
		return ret

	def __getitem__(self, key):
		# self.checkUpdate()

		baseDictKeys = list(self.dirDicts.keys())
		baseDictKeys.sort()
		for dirDictKey in baseDictKeys:

			# keyLUT = self.filterNameThroughDB(key)
			keyLUT = self.filterNameThroughDB(key)

			if keyLUT in self.dirDicts[dirDictKey]:
				tmp = self.dirDicts[dirDictKey][keyLUT]
				return self._processItemIntoRet(tmp, key, keyLUT, dirDictKey)

		return {"fqPath" : None, "item": None, "inKey" : None, "dirKey": None, "rating": None}

	def __contains__(self, key):
		# self.checkUpdate()

		baseDictKeys = list(self.dirDicts.keys())
		baseDictKeys.sort()
		for dirDictKey in baseDictKeys:
			if key in self.dirDicts[dirDictKey]:
				return key in self.dirDicts[dirDictKey]

		return False

	def __len__(self):
		ret = 0
		for dirDictKey in self.dirDicts.keys():
			ret += self.dirDicts[dirDictKey]
		return ret




nameLookup = MapWrapper("mangaNameMappings")
dirsLookup = MapWrapper("folderNameMappings")
dirNameProxy = DirNameProxy(settings.mangaFolders)



if __name__ == "__main__":
	logSetup.initLogging()
	print("wat")
	dirNameProxy.checkUpdate(force=True)
	dirNameProxy.checkUpdate()
	print("running")


	names = set(["fractale", "fractale", "fractale", "fractale", "fractale", "kaze to ki no uta", "boku ni koi suru mechanical", "kaze to ki no uta", "boku ni koi suru mechanical", "magi", "k - days of blue", "k - days of blue", "gurenki - creo the crimson crises", "gurenki - creo the crimson crises", "soredemo sekai wa utsukushii", "gurenki - creo the crimson crises", "fuuka", "claymore", "himeyaka na tousaku", "himeyaka na tousaku", "himeyaka na tousaku", "kyoushi mo iroiro aru wake de", "ah my goddess", "akb49", "koroshiya ichi bangaihen", "koroshiya ichi bangaihen", "koi no okite"])
	print (names)
	for keyTmp, stats in dirNameProxy.iteritems():
		if keyTmp in names:
			print("Item in dict? ", keyTmp)

	for nameTmp in names:
		if nameTmp in dirNameProxy:
			print("Have name", nameTmp)
		else:
			print("Do not have name", nameTmp)


	# try:
	# 	while True:
	# 		time.sleep(1)
	# 		dirNameProxy.checkUpdate()
	# except KeyboardInterrupt:
	# 	pass
	# print("Complete?")
		# print item


