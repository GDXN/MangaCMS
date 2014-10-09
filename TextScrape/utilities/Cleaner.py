
import logSetup
if __name__ == "__main__":
	print("Initializing logging")
	logSetup.initLogging()

import TextScrape.TextScrapeBase
import os.path
import os
import signal
import sys
import shutil
import runStatus
import hashlib
import settings

class DbFix(TextScrape.TextScrapeBase.TextScraper):

	tableKey   = 'none'
	loggerPath = 'Main.Util'
	pluginName = 'DbFixer'
	badwords   = None
	baseUrl    = None
	startUrl   = None

	def getNonhashedFiles(self):
		self.log.info("Querying for file items without hashes")

		with self.conn.cursor() as cur:
			with TextScrape.TextScrapeBase.transaction(cur, commit=True):
				cur.execute("SELECT dbid,fspath,url,src FROM {tableName} WHERE fhash IS NULL and istext=FALSE;".format(tableName=self.tableName))
				ret = cur.fetchall()

		self.log.info("Found %s unhashed items", len(ret))
		return ret


	def updateWithHash(self, src, dbId, fHash):

		# Update tablekey to match item in question.
		self.tableKey = src

		with self.conn.cursor() as cur:
			with TextScrape.TextScrapeBase.transaction(cur):
				cur.execute("SELECT fspath FROM {tableName} WHERE fhash=%s;".format(tableName=self.tableName), (fHash, ))
				ret = cur.fetchall()

		if ret:
			print("Wat?", ret[0][0])
			self.updateDbEntry(dbid=dbId, fhash=fHash, fspath=ret[0][0])
			return

		self.updateDbEntry(dbid=dbId, fhash=fHash)

	def hashUnlinked(self):
		toHash = self.getNonhashedFiles()

		toHash = [(fsPath, dbId, src) for dbId, fsPath, url, src in toHash]
		toHash.sort()
		for fsPath, dbId, src in toHash:
			if not os.path.exists(fsPath):
				self.log.info("Item with dbId=%s doesn't exist?", dbId)
				self.deleteDbEntry(dbid=dbId)
				continue

			with open(fsPath, "rb") as fp:
				fHash = self.getHash(fp.read())
				print(fsPath, fHash)
				self.updateWithHash(src, dbId, fHash)


	# Tools to allow conversion of url column to CITEXT
	def dedupCase(self):
		with self.conn.cursor() as cur:
			with TextScrape.TextScrapeBase.transaction(cur, commit=True):
				cur.execute("SELECT dbid,url FROM {tableName};".format(tableName=self.tableName))
				ret = cur.fetchall()
		print(len(ret))

		ret.sort(reverse=True)

		items = {}
		for dbId, url in ret:
			url = url.upper()
			if url in items:
				print("Should delete for url", dbId, items[url], url)
				self.deleteDbEntry(dbid=dbId)
			else:
				items[url] = dbId

	def getDbPaths(self):
		self.log.info("Querying for database file items")

		with self.conn.cursor() as cur:
			with TextScrape.TextScrapeBase.transaction(cur, commit=True):
				cur.execute("SELECT dbid,fspath,fhash FROM {tableName} WHERE istext=FALSE;".format(tableName=self.tableName))
				items = cur.fetchall()

		self.log.info("Found %s file items", len(items))

		ret = {}

		for dbId, fsPath, fHash in items:
			if not fsPath in ret:
				ret[fsPath] = [(dbId, fHash)]
			else:
				ret[fsPath].append((dbId, fHash))

		self.log.info("Processed into return dict")
		return ret


	def getFsPaths(self):
		ret = set()
		self.log.info("Scanning for filesystem items")
		for root, dirs, files in os.walk(settings.bookCachePath):
			for filen in files:
				ret.add(os.path.join(root, filen))

		self.log.info("Found %s files on cache path", len(ret))
		return ret


	def removeMissingFiles(self):

		dbItems = self.getDbPaths()
		fsItems = self.getFsPaths()

		for fsPath, arr in dbItems.items():
			if not os.path.exists(fsPath):
				print("DB Item that doesn't exist as a file? Removing from DB", fsPath)
				with self.conn.cursor() as cur:
					with TextScrape.TextScrapeBase.transaction(cur, commit=True):
						cur.execute("DELETE FROM {tableName} WHERE dbid=%s;".format(tableName=self.tableName), (arr[0], ))


		for filen in fsItems:
			if not filen in dbItems:
				print("FS Item that doesn't exist in db? Deleting", filen)
				os.unlink(filen)

	def checkForDuplicatesByHash(self):

		dbItems = self.getDbPaths()

		hashdict = {}
		for fsPath, arr in dbItems.items():

			dummy_dbid, fhash = arr[0]
			if fhash in hashdict and hashdict[fhash] != fsPath:
				print("Duplicate?", fsPath, arr)
			else:
				hashdict[fhash] = fsPath


def customHandler(dummy_signum, dummy_stackframe):
	if runStatus.run:
		runStatus.run = False
		print("Telling threads to stop")
	else:
		print("Multiple keyboard interrupts. Raising")
		raise KeyboardInterrupt


def test():

	signal.signal(signal.SIGINT, customHandler)

	if len(sys.argv) < 2:
		print("This script requires command line parameters")

		return

	mainArg = sys.argv[1]

	print ("Passed arg", mainArg)

	scrp = DbFix()


	if mainArg.lower() == "hash-files":
		scrp.hashUnlinked()
	elif mainArg.lower() == "hash-check":
		scrp.checkForDuplicatesByHash()
	elif mainArg.lower() == "remove-missing":
		scrp.removeMissingFiles()
	elif mainArg.lower() == "dedup-case":
		scrp.dedupCase()
	else:
		print("Unknown arg!")




if __name__ == "__main__":
	test()

