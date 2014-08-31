

import re

import settings
import logging
import psycopg2
import time
import logSetup
import threading
import os
import os.path

import unicodedata

import pyinotify

import random
random.seed()

# --------------------------------------------------------------

# Asshole scanlators who don't put their name in "[]"
# Fuck you people. Seriously
shitScanlators = ["rhs", "rh", "mri", "rhn", "se", "rhfk", "mw-rhs"]

chapVolRe     = re.compile(r"(?:(?:ch?|v(?:ol(?:ume)?)?|(?:ep)|(?:stage)|(?:pa?r?t)|(?:chapter)|(?:story)|(?:extra)|(?:load)|(?:log)) ?\d+)", re.IGNORECASE)
trailingNumRe = re.compile(r"(\d+$)", re.IGNORECASE)

def guessSeriesFromFilename(inStr):
	inStr = inStr.lower()
	# if there is a "." in the last 6 chars, it's probably an extension. remove it.
	inStr = removeBrackets(inStr)

	if "." in inStr[-6:]:
		inStr, dummy_ext = inStr.rsplit(".", 1)

	for shitScanlator in shitScanlators:
		if inStr.lower().endswith(shitScanlator.lower()):
			inStr = inStr[:len(shitScanlator)*-1]

	inStr = inStr.replace("+", " ")
	inStr = inStr.replace("_", " ")
	inStr = inStr.replace("the4koma", " ")
	inStr = inStr.replace("4koma", " ")

	inStr = stripChapVol(inStr)

	inStr = inStr.strip()
	inStr = stripTrailingNumbers(inStr)

	inStr = prepFilenameForMatching(inStr)
	return inStr

def stripChapVol(inStr):
	inStr = chapVolRe.sub(" ", inStr)
	return inStr
def stripTrailingNumbers(inStr):
	inStr = trailingNumRe.sub(" ", inStr)
	return inStr

# Execution time of ~ 0.000052889607680 second (52 microseconds)
def prepFilenameForMatching(inStr):
	inStr = makeFilenameSafe(inStr)
	inStr = sanitizeString(inStr)
	return inStr.lower()

def makeFilenameSafe(inStr):


	inStr = inStr.replace("%20", " ") \
				 .replace("<",  " ") \
				 .replace(">",  " ") \
				 .replace(":",  " ") \
				 .replace("\"", " ") \
				 .replace("/",  " ") \
				 .replace("\\", " ") \
				 .replace("|",  " ") \
				 .replace("?",  " ") \
				 .replace("*",  " ") \
				 .replace('"', " ")

	# FUCK YOU SMART-QUOTES.
	inStr = inStr.replace("“",  "\"") \
				 .replace("”",  "\"")


	# Collapse all the repeated spaces down.
	while inStr.find("  ")+1:
		inStr = inStr.replace("  ", " ")

	inStr = inStr.rstrip(".")  # Windows file names can't end in dot. For some reason.
	inStr = inStr.strip(" ")   # And can't have leading or trailing spaces

	return inStr

def cleanUnicode(inStr):
	return unicodedata.normalize("NFKD", inStr).encode("ascii", errors="ignore").decode()


bracketStripRe = re.compile(r"(\[[\+\~\-\!\d\w &:]*\])")

def removeBrackets(inStr):
	inStr = bracketStripRe.sub(" ", inStr)
	while inStr.find("  ")+1:
		inStr = inStr.replace("  ", " ")
	return inStr

# Basically used for dir-path cleaning to prep for matching, and not much else
def sanitizeString(inStr, flatten=True):
	baseName = removeBrackets(inStr)				#clean brackets

	if flatten:
		baseName = baseName.replace("~", "")		 # Spot fixes. We'll see if they break anything
		baseName = baseName.replace(".", "")
		baseName = baseName.replace(";", "")
		baseName = baseName.replace(":", "")
		baseName = baseName.replace("-", "")
		baseName = baseName.replace("?", "")
		baseName = baseName.replace("!", "")
		baseName = baseName.replace('"', "")
		baseName = baseName.replace("'", "")

	# baseName = baseName.replace("'", "")
	while baseName.find("  ")+1:
		baseName = baseName.replace("  ", " ")

	# baseName = unicodedata.normalize('NFKD', baseName).encode("ascii", errors="ignore")  # This will probably break shit


	return baseName.lower().strip()

def extractRating(inStr):
	# print("ExtractRating = '%s', '%s'" % (inStr, type(inStr)))
	search = re.search(r"^(.*?)\[([~+\-!]+)\](.*?)$", inStr)
	if search:
		# print("Found rating! Prefix = {pre}, rating = {rat}, postfix = {pos}".format(pre=search.group(1), rat=search.group(2), pos=search.group(3)))
		return search.group(1), search.group(2), search.group(3)
	else:
		return inStr, "", ""

def ratingStrToInt(inStr):


	pos = inStr.count("+")
	neg = inStr.count("-")

	return pos - neg

def extractRatingToInt(inStr):
	dummy, rating, dummy = extractRating(inStr)
	if not rating:
		return 0
	return ratingStrToInt(rating)


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
		"mangaNameMappings"  : ["manganamemappings",
								'''(mangaUpdates text NOT NULL,
									mangaTraders text NOT NULL,
									PRIMARY KEY(mangaTraders) ON CONFLICT REPLACE)''',
								 ("mangaUpdates", "mangaTraders")],
		"folderNameMappings" : ["foldernamemappings",
								'''(baseName text NOT NULL,
									folderName text NOT NULL,
									PRIMARY KEY(baseName, folderName) ON CONFLICT REPLACE)''',
								("baseName", "folderName")]

	}

	def __init__(self, tableName):
		self.__dict__ = self._shared_state

		self.updateLock = threading.Lock()

		if not tableName in self.validTables:
			raise ValueError("Invalid table name specified!")

		self.log.info("Loading NSLookup")
		self.tableName = self.validTables[tableName][0]
		self.tableSchema = self.validTables[tableName][1]
		self.tableCols = self.validTables[tableName][2]
		self.openDB()

		self.lastUpdate = 0
		self.items = {}
		self.updateFromDB()

	def stop(self):
		self.log.info("Unoading NSLookup")
		self.closeDB()

	def openDB(self):
		self.log.info( "NSLookup Opening DB...",)
		self.conn = psycopg2.connect(dbname=settings.DATABASE_DB_NAME, user=settings.DATABASE_USER,password=settings.DATABASE_PASS)
		self.conn.autocommit = True
		self.log.info("opened")

		with self.conn.cursor() as cur:
			cur.execute('''SELECT tablename FROM pg_catalog.pg_tables WHERE tablename='%s';''' % self.tableName)
			rets = cur.fetchall()

		if rets:
			rets = rets[0]
		if not self.tableName in rets:   # If the DB doesn't exist, set it up.
			self.log.info("DB Not setup for %s. Creating table", self.tableName)
			# cur = self.conn.cursor()
			# cur.execute('''CREATE TABLE %s %s''' % (self.tableName, self.tableSchema))
			# cur.commit()
			raise ValueError("%s Database does not exist. Name mapper cannot work." % self.tableName)

		self.log.info("PRAGMA return value = %s", rets)

	def closeDB(self):
		self.log.info( "Closing DB...")
		self.conn.close()
		self.log.info( "done")

	def updateFromDB(self, force=False):
		# Only query the database at most once per 5 seconds.
		if time.time() > self.lastUpdate + 5 or force:
			self.updateLock.acquire()
			self.log.info("NSLookupTool updating from DB. Update forced: %s", force)

			with self.conn.cursor() as cur:
				cur.execute('SELECT %s, %s FROM %s;' % (self.tableCols[0], self.tableCols[1], self.tableName))
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



# proxy that makes a DB look like a dict
# Opens a dynamically specifiable database, though the database must be one of a predefined set.
class MtNamesMapWrapper(object):


	log = logging.getLogger("Main.NSLookup")

	dbPath = settings.dbName

	modes = {
		"buId->fsName" : {"cols" : ["buId", "fsSafeName"], "table" : 'munamelist'},
		"buId->name"   : {"cols" : ["buId", "name"],       "table" : 'munamelist'},
		"fsName->buId" : {"cols" : ["fsSafeName", "buId"], "table" : 'munamelist'},
		"buId->buName" : {"cols" : ["buId", "buName"],     "table" : 'mangaseries'},
		"buName->buId" : {"cols" : ["buName", "buId"],     "table" : 'mangaseries'}
	}

	def __init__(self, mode):


		self.updateLock = threading.Lock()


		self.log.info("Loading NSLookup")

		if not mode in self.modes:
			raise ValueError("Specified mapping mode not valid")
		self.mode = self.modes[mode]
		self.openDB()

		self.lastUpdate = 0
		self.items = {}

		self.queryStr = 'SELECT %s FROM %s WHERE %s=%%s;' % (self.mode["cols"][1], self.mode["table"], self.mode["cols"][0])
		self.allQueryStr = 'SELECT %s, %s FROM %s;' % (self.mode["cols"][0], self.mode["cols"][1], self.mode["table"])
		self.log.info("Mode %s, Query %s", mode, self.queryStr)
		self.log.info("Mode %s, IteratorQuery %s",  mode, self.allQueryStr)


	def stop(self):
		self.log.info("Unoading NSLookup")
		self.closeDB()

	def openDB(self):
		self.log.info( "NSLookup Opening DB...",)
		self.conn = psycopg2.connect(dbname=settings.DATABASE_DB_NAME, user=settings.DATABASE_USER,password=settings.DATABASE_PASS)
		self.conn.autocommit = True
		self.log.info("opened")

		with self.conn.cursor() as cur:
			cur.execute('''SELECT tablename FROM pg_catalog.pg_tables WHERE tablename='%s';''' % self.mode["table"])
			rets = cur.fetchall()
		if rets:
			rets = rets[0]
		if not self.mode["table"] in rets:   # If the DB doesn't exist, set it up.
			self.log.info("DB Not setup for %s.", self.mode["table"])
			raise ValueError

	def closeDB(self):
		self.log.info( "Closing DB...")
		self.conn.close()
		self.log.info( "done")

	def iteritems(self):


		with self.conn.cursor() as cur:
			cur.execute(self.allQueryStr)
			rets = cur.fetchall()

		for fsSafeName, buId in rets:
			yield fsSafeName, buId


	def __getitem__(self, key):

		if "keyfunc" in self.mode:
			key = self.mode["keyfunc"](key)

		with self.conn.cursor() as cur:
			cur.execute(self.queryStr, (key, ))
			rets = cur.fetchall()

		if not rets:
			return []
		return set([item[0] for item in rets])

	def __contains__(self, key):

		if self[key] != None:
			return True
		return False




class EventHandler(pyinotify.ProcessEvent):
	def __init__(self, paths):
		super(EventHandler, self).__init__()
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

	# test-mode is when the unittesting system pre-loads the dir-dict with known values,
	# so we don't have to start the dir observers (sloooow).
	# Therefore, in test-mode, we don't check if the observers exist.
	testMode = False

	def __init__(self, paths):
		self.__dict__ = self._shared_state

		self.notifierRunning = False
		self.updateLock = threading.Lock()


		self.paths = paths

		self.lastCheck = 0
		self.maxRate = 5
		self.dirDicts = {}


		# for watch in self.

	def observersActive(self):
		return self.notifierRunning

	def startDirObservers(self):

		# Eventually, I want to use this to prevent crashes if the observers
		# have not been started. Eventually.

		self.notifierRunning = True

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

		self.checkUpdate(force=True)
		baseDictKeys = list(self.dirDicts.keys())
		baseDictKeys.sort()

	def stop(self):
		# Only stop once (should prevent on-exit errors)
		if self.notifierRunning:
			self.log.info("Unoading DirLookup")
			self.notifier.stop()
			self.notifierRunning = False

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
				baseName = getCanonicalMangaUpdatesName(baseName)
				baseName = prepFilenameForMatching(baseName)

				targets[baseName] = fullPath

			# print("Linking '%s' to '%s'" % (fullPath, baseName))
		self.log.info( "Done")


		return targets

	def manuallyLoadDirDict(self, dirItems):
		tmp = {}
		self.testMode = True
		for name in dirItems:

			baseName = prepFilenameForMatching(name)
			baseName = getCanonicalMangaUpdatesName(baseName)
			baseName = prepFilenameForMatching(baseName)
			tmp[baseName] = name

		self.dirDicts[0] = tmp


	def checkUpdate(self, force=False, skipTime=False):

		updateTime = time.time()
		if not updateTime > (self.lastCheck + self.maxRate) and (not force) and (not skipTime):
			# print("DirDicts not stale!")
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

	# Force the update of the directory containing the passed path dirPath
	# Useful for when programmatic changes are made, such as creating a directory, and
	# you want to force that change to be recognized in the dir proxy immediately.
	# This is needed because the change-watching mechanism doesn't always seem
	# to properly catch folder creation or manipulation.
	# It works great for file changes.
	def forceUpdateContainingPath(self, dirPath):

		keys = list(self.paths.keys())
		keys.sort()
		for key in keys:
			if self.paths[key]["dir"] in dirPath:
				self.log.info("DirLookupTool updating %s, path=%s!", key, self.paths[key]["dir"])
				self.log.info("DirLookupTool updating from Directory")
				self.dirDicts[key] = self.getDirDict(self.paths[key]["dir"])
				self.paths[key]["lastScan"] = time.time()


	def changeRating(self, mangaName, newRating):
		item = self[mangaName]
		if not item['fqPath']:
			raise ValueError("Invalid item")

		print("Item", item)
		print("Path", self.paths[item['sourceDict']]['dir'])
		oldPath = item['fqPath']
		self.changeRatingPath(oldPath, newRating)

	def _checkLookupNewDir(self, fromPath):
		for key in settings.ratingsSort["fromkey"]:
			if fromPath.startswith(settings.mangaFolders[key]["dir"]):
				fromBase = settings.mangaFolders[key]["dir"]
				toBase   = settings.mangaFolders[settings.ratingsSort["tokey"]]["dir"]
				print("Replacing base '%s with base '%s" % (fromBase, toBase))
				return fromPath.replace(fromBase, toBase)

		# If we don't have a directory we want to replace, we just return the string as passed
		return fromPath

	def changeRatingPath(self, oldPath, newRating):

		tmpPath = oldPath
		if hasattr(settings, "ratingsSort"):
			if newRating >= settings.ratingsSort["thresh"]:
					tmpPath = self._checkLookupNewDir(oldPath)

		prefix, dummy_rating, postfix = extractRating(tmpPath)

		if newRating == 0:
			return


		# print("Rating change call!")
		if newRating > 0 and newRating <= 5:
			ratingStr = "+"*newRating
		elif newRating == 0:
			ratingStr = ""
		elif newRating < 0 and newRating > -6:
			ratingStr = "-"*abs(newRating)
		else:
			raise ValueError("Invalid rating value!")

		if len(ratingStr):
			ratingStr = " [{rat}] ".format(rat=ratingStr)

		newPath = "{pre}{rat}{pos}".format(pre=prefix, rat=ratingStr, pos=postfix)
		newPath = newPath.rstrip(" ").lstrip(" ")

		# print("Oldpath = ", oldPath)
		# print("Newpath = ", newPath)
		if oldPath != newPath:
			if os.path.exists(newPath):
				raise ValueError("New path exists already!")
			else:
				os.rename(oldPath, newPath)
				self.eventH.setPathDirty(os.path.split(oldPath)[0])
				print("Calling checkUpdate")
				self.checkUpdate(skipTime=True)
				print("checkUpdate Complete")


	def filterPreppedNameThroughDB(self, name):
		if not self.notifierRunning and self.testMode == False:
			self.log.warning("Directory observers not started! No directory contents will have been loaded!")
		name = getCanonicalMangaUpdatesName(name)
		name = prepFilenameForMatching(name)
		return name

	def getUnsanitizedName(self, name):
		name = self.filterPreppedNameThroughDB(name)
		return self[name]

	def getPathByKey(self, key):
		return self.paths[key]

	def getDirDicts(self):
		return self.dirDicts

	def getRawDirDict(self, key):
		return self.dirDicts[key]

	def getFromSpecificDict(self, dictKey, itemKey):
		filteredKey = self.filterPreppedNameThroughDB(itemKey)
		# print("Key = ", dictKey, filteredKey,  filteredKey in self.dirDicts[dictKey])
		if filteredKey in self.dirDicts[dictKey]:
			tmp = self.dirDicts[dictKey][filteredKey]
			return self._processItemIntoRet(tmp, itemKey, filteredKey, dictKey)

		return {"fqPath" : None, "item": None, "inKey" : None, "dirKey": filteredKey, "rating": None, "sourceDict": None}



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

	def getTotalItems(self):
		items = 0
		for item in self.dirDicts.values():
			items += len(item)
		return items

	def random(self):
		items = self.getTotalItems()
		index = random.randint(0, items-1)
		# print("Getting random item with indice", index)
		return self.getByIndex(index)

	def getByIndex(self, index):
		if index < 0 or index >= self.getTotalItems():
			raise ValueError("Index value exceeds allowable range - %s" % index)
		for dummy_key, itemSet in self.dirDicts.items():
			if index > len(itemSet):
				index -= len(itemSet)
				continue
			else:
				item = itemSet[list(itemSet.keys())[index]]
				dummy_basePath, dirName = os.path.split(item)
				# print("Selected item with dirPath: ", item)
				filteredKey = prepFilenameForMatching(dirName)
				return self[filteredKey]
		raise ValueError("Exceeded valid range?")

	def __getitem__(self, key):
		# self.checkUpdate()

		baseDictKeys = list(self.dirDicts.keys())
		baseDictKeys.sort()
		keyLUT = self.filterPreppedNameThroughDB(key)

		for dirDictKey in baseDictKeys:
			# keyLUT = self.filterPreppedNameThroughDB(key)

			if keyLUT in self.dirDicts[dirDictKey]:
				tmp = self.dirDicts[dirDictKey][keyLUT]
				return self._processItemIntoRet(tmp, key, keyLUT, dirDictKey)

		return {"fqPath" : None, "item": None, "inKey" : key, "dirKey": keyLUT, "rating": None}

	def __contains__(self, key):
		# self.checkUpdate()

		key = self.filterPreppedNameThroughDB(key)

		baseDictKeys = list(self.dirDicts.keys())
		baseDictKeys.sort()
		for dirDictKey in baseDictKeys:

			# Limit scanned items to < 100
			if dirDictKey > 99:
				continue

			if key in self.dirDicts[dirDictKey]:
				return key in self.dirDicts[dirDictKey]

		return False

	def __len__(self):
		ret = 0
		for dirDictKey in self.dirDicts.keys():
			ret += self.dirDicts[dirDictKey]
		return ret



## If we have the series name in the synonym database, look it up there, and use the ID
## to fetch the proper name from the MangaUpdates database
def getCanonicalMangaUpdatesName(sourceSeriesName):

	fsName = prepFilenameForMatching(sourceSeriesName)
	mId = buIdLookup[fsName]
	if mId and len(mId) == 1:
		correctSeriesName = idLookup[mId.pop()]
		if correctSeriesName and len(correctSeriesName) == 1:
			return correctSeriesName.pop()
	return sourceSeriesName



## If we have the series name in the synonym database, look it up there, and use the ID
## to fetch the proper name from the MangaUpdates database
def haveCanonicalMangaUpdatesName(sourceSeriesName):

	fsName = prepFilenameForMatching(sourceSeriesName)
	mId = buIdLookup[fsName]
	if mId and len(mId) == 1:
		return True
	mId = buIdFromName[sourceSeriesName]

	if mId and len(mId) == 1:
		return True
	return False


buIdLookup       = MtNamesMapWrapper("fsName->buId")
buSynonymsLookup = MtNamesMapWrapper("buId->name")
idLookup         = MtNamesMapWrapper("buId->buName")
buIdFromName     = MtNamesMapWrapper("buName->buId")

nameLookup       = MapWrapper("mangaNameMappings")
dirsLookup       = MapWrapper("folderNameMappings")
dirNameProxy     = DirNameProxy(settings.mangaFolders)




def testNameTools():
	import unittest


	class TestSequenceFunctions(unittest.TestCase):

		def setUp(self):
			dirNameProxy.startDirObservers()

		def test_name_001(self):
			self.assertTrue("Danshi Koukousei no Nichijou" in dirNameProxy)




	unittest.main()




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


