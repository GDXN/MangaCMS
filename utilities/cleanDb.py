import sys
sys.path.insert(0,"..")
import os.path

import logSetup
if __name__ == "__main__":
	logSetup.initLogging()


import runStatus

import ScrapePlugins.DbBase
import nameTools as nt
import sys
import signal


class PathCleaner(ScrapePlugins.DbBase.DbBase):
	loggerPath = "Main.Pc"
	tableName  = "MangaItems"


	def moveFile(self, srcPath, dstPath):
		dlPath, fName = os.path.split(srcPath)
		print("dlPath, fName", dlPath, fName)
		cur = self.conn.cursor()

		cur.execute("BEGIN;")
		cur.execute("SELECT dbId FROM {tableName} WHERE downloadPath=%s AND fileName=%s".format(tableName=self.tableName), (dlPath, fName))
		ret = cur.fetchall()

		if not ret:
			cur.execute("COMMIT;")
			return
		dbId = ret.pop()

		cur.execute("UPDATE {tableName} SET downloadPath=%s, fileName=%s WHERE dbId=%s".format(tableName=self.tableName), (dlPath, fName, dbId))
		cur.execute("COMMIT;")
		self.log.info("Moved file in local DB.")

	def updatePath(self, dbId, dlPath):

		cur = self.conn.cursor()

		cur.execute("BEGIN;")

		cur.execute("UPDATE {tableName} SET downloadPath=%s WHERE dbId=%s".format(tableName=self.tableName), (dlPath, dbId))
		cur.execute("COMMIT;")
		self.log.info("Moved file in local DB.")

	def findIfMigrated(self, filePath):
		dirPath, fileName = os.path.split(filePath)

		series = dirPath.split("/")[-1]
		series = nt.getCanonicalMangaUpdatesName(series)
		otherDir = nt.dirNameProxy[series]

		if not otherDir["fqPath"]:
			return False
		if otherDir["fqPath"] == dirPath:
			return False

		newPath = os.path.join(otherDir["fqPath"], fileName)
		if os.path.exists(newPath):
			print("File moved!")
			return otherDir["fqPath"]

		return False

	def resetDlState(self, dbId, newState):
		with self.conn.cursor() as cur:
			cur.execute("UPDATE {tableName}  SET dlState=%s WHERE dbId=%s".format(tableName=self.tableName), (newState, dbId))

	def resetMissingDownloads(self):

		alterSites = ["bt", "jz", "mc"]

		if not nt.dirNameProxy.observersActive():
			nt.dirNameProxy.startDirObservers()


		cur = self.conn.cursor()


		cur.execute("BEGIN;")
		cur.execute("SELECT dbId, sourceSite, downloadPath, fileName, tags FROM {tableName} WHERE dlState=%s".format(tableName=self.tableName), (2, ))
		ret = cur.fetchall()

		cur.execute("COMMIT;")

		cur.execute("BEGIN;")

		print("Ret", len(ret))

		loops = 0
		for dbId, sourceSite, downloadPath, fileName, tags in ret:
			filePath = os.path.join(downloadPath, fileName)
			if tags == None:
				tags = ""
			if "deleted" in tags or "was-duplicate" in tags:
				continue

			if not os.path.exists(filePath):
				migPath = self.findIfMigrated(filePath)
				if not migPath:
					if sourceSite in alterSites:
						print("Resetting download for ", filePath, "source=", sourceSite)
						self.resetDlState(dbId, 0)

					else:
						print("Missing", filePath)
				else:
					print("Moved!")
					print("		Old = '%s'" % filePath)
					print("		New = '%s'" % migPath)
					self.updatePath(dbId, migPath)

			loops += 1
			if loops % 1000 == 0:
				cur.execute("COMMIT;")
				print("Incremental Commit!")
				cur.execute("BEGIN;")

		cur.execute("COMMIT;")

	def updateTags(self, dbId, newTags):
		cur = self.conn.cursor()
		cur.execute("UPDATE {tableName} SET tags=%s WHERE dbId=%s;".format(tableName=self.tableName), (newTags, dbId))


	def clearInvalidDedupTags(self):


		cur = self.conn.cursor()
		cur.execute("BEGIN;")
		print("Querying")
		cur.execute("SELECT dbId, downloadPath, fileName, tags FROM {tableName}".format(tableName=self.tableName))
		print("Queried. Fetching results")
		ret = cur.fetchall()
		cur.execute("COMMIT;")
		print("Have results. Processing")

		cur.execute("BEGIN;")
		for  dbId, downloadPath, fileName, tags in ret:
			if tags == None: tags = ""
			if "deleted" in tags and "was-duplicate" in tags:
				fPath = os.path.join(downloadPath, fileName)
				if os.path.exists(fPath):
					tags = set(tags.split(" "))
					tags.remove("deleted")
					tags.remove("was-duplicate")
					tags = " ".join(tags)
					print("File ", fPath, "exists!", dbId, )
					self.updateTags(dbId, tags)

		cur.execute("COMMIT;")

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
		print("Args:")
		print("	'reset-missing' - Reset downloads where the file is missing, and the download is not tagged as deduplicated.")
		print("	'clear-bad-dedup' - Remove deduplicated tag from any files where the file exists.")
		return

	mainArg = sys.argv[1]

	print ("Passed arg", mainArg)


	pc = PathCleaner()
	pc.openDB()

	if mainArg.lower() == "reset-missing":
		pc.resetMissingDownloads()
	elif mainArg.lower() == "clear-bad-dedup":
		pc.clearInvalidDedupTags()
	else:
		print("Unknown arg!")

	pc.closeDB()

if __name__ == "__main__":
	try:
		test()
	finally:
		pass
		# import nameTools as nt
		# nt.dirNameProxy.stop()

