import sys
sys.path.insert(0,"..")
import os.path

import logSetup
if __name__ == "__main__":
	logSetup.initLogging()


import runStatus
runStatus.preloadDicts = False


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

		alterSites = ["bt", "jz", "mc", "mk", "irc-irh"]

		if not nt.dirNameProxy.observersActive():
			nt.dirNameProxy.startDirObservers()


		cur = self.conn.cursor()


		cur.execute("BEGIN;")
		cur.execute("SELECT dbId, sourceSite, downloadPath, fileName, tags FROM {tableName} WHERE dlState=%s ORDER BY retreivalTime DESC;".format(tableName=self.tableName), (2, ))
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
						print("Missing", filePath, "from", sourceSite)
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



	def patchBatotoLinks(self):


		cur = self.conn.cursor()
		cur.execute("BEGIN;")
		print("Querying")
		cur.execute("SELECT dbId, sourceUrl FROM {tableName} WHERE sourceSite='bt';".format(tableName=self.tableName))
		print("Queried. Fetching results")
		ret = cur.fetchall()
		cur.execute("COMMIT;")
		print("Have results. Processing")

		cur.execute("BEGIN;")
		for  dbId, sourceUrl in ret:
			if "batoto" in sourceUrl.lower():
				sourceUrl = sourceUrl.replace("http://www.batoto.net/", "http://bato.to/")
				print("Link", sourceUrl)

				cur.execute("SELECT dbId FROM {tableName} WHERE sourceUrl=%s;".format(tableName=self.tableName), (sourceUrl, ))
				ret = cur.fetchall()
				if not ret:
					print("Updating")
					cur.execute("UPDATE {tableName} SET sourceUrl=%s WHERE dbId=%s;".format(tableName=self.tableName), (sourceUrl, dbId))

				else:
					print("Replacing")
					cur.execute("DELETE FROM {tableName} WHERE sourceUrl=%s;".format(tableName=self.tableName), (sourceUrl, ))
					cur.execute("UPDATE {tableName} SET sourceUrl=%s WHERE dbId=%s;".format(tableName=self.tableName), (sourceUrl, dbId))


		cur.execute("COMMIT;")




	def insertNames(self, buId, names):

		with self.conn.cursor() as cur:
			for name in names:
				fsSafeName = nt.prepFilenameForMatching(name)
				cur.execute("""SELECT COUNT(*) FROM munamelist WHERE buId=%s AND name=%s;""", (buId, name))
				ret = cur.fetchone()
				if not ret[0]:
					cur.execute("""INSERT INTO munamelist (buId, name, fsSafeName) VALUES (%s, %s, %s);""", (buId, name, fsSafeName))
				else:
					print("wat", ret[0], bool(ret[0]))

	def crossSyncNames(self):

		cur = self.conn.cursor()
		cur.execute("BEGIN;")
		print("Querying")
		cur.execute("SELECT DISTINCT ON (buname) buname, buId FROM mangaseries ORDER BY buname, buid;")
		print("Queried. Fetching results")
		ret = cur.fetchall()
		cur.execute("COMMIT;")
		print("Have results. Processing")

		cur.execute("BEGIN;")

		missing = 0
		for item in ret:
			buName, buId = item
			if not buName:
				continue

			cur.execute("SELECT * FROM munamelist WHERE name=%s;", (buName, ))
			ret = cur.fetchall()
			# mId = nt.getMangaUpdatesId(buName)

			if not ret:
				print("Item missing '{item}', mid:{mid}".format(item=item, mid=ret))
				self.insertNames(buId, [buName])
				missing += 1

			if not runStatus.run:
				break
				# print("Item '{old}', '{new}', mid:{mid}".format(old=item, new=nt.getCanonicalMangaUpdatesName(item), mid=mId))
		print("Total: ", len(ret))
		print("Missing: ", missing)


	def consolidateSeriesNaming(self):


		cur = self.conn.cursor()
		# cur.execute("BEGIN;")
		# print("Querying")
		# cur.execute("SELECT DISTINCT(seriesName) FROM {tableName};".format(tableName=self.tableName))
		# print("Queried. Fetching results")
		# ret = cur.fetchall()
		# cur.execute("COMMIT;")
		# print("Have results. Processing")

		# for item in ret:
		# 	item = item[0]
		# 	if not item:
		# 		continue

		# 	mId = nt.getMangaUpdatesId(item)
		# 	if not mId:
		# 		print("Item '{old}', '{new}', mid:{mid}".format(old=item, new=nt.getCanonicalMangaUpdatesName(item), mid=mId))
		# print("Total: ", len(ret))

		items = ["Murciélago", "Murcielago", "Murciélago"]

		for item in items:
			print("------", item, nt.getCanonicalMangaUpdatesName(item), nt.haveCanonicalMangaUpdatesName(item))

		# cur.execute("BEGIN;")
		# print("Querying")
		# cur.execute("SELECT DISTINCT ON (buname) buname, buId FROM mangaseries ORDER BY buname, buid;")
		# print("Queried. Fetching results")
		# ret = cur.fetchall()
		# cur.execute("COMMIT;")
		# print("Have results. Processing")

		# cur.execute("BEGIN;")

		# missing = 0
		# for item in ret:
		# 	buName, buId = item
		# 	if not buName:
		# 		continue

		# 	cur.execute("SELECT * FROM munamelist WHERE name=%s;", (buName, ))
		# 	ret = cur.fetchall()
		# 	# mId = nt.getMangaUpdatesId(buName)

		# 	if not ret:
		# 		print("Item missing '{item}', mid:{mid}".format(item=item, mid=ret))
		# 		self.insertNames(buId, [buName])
		# 		missing += 1

		# 	if not runStatus.run:
		# 		break
		# 		# print("Item '{old}', '{new}', mid:{mid}".format(old=item, new=nt.getCanonicalMangaUpdatesName(item), mid=mId))
		# print("Total: ", len(ret))
		# print("Missing: ", missing)


		# for  dbId, sourceUrl in ret:
		# 	if "batoto" in sourceUrl.lower():
		# 		sourceUrl = sourceUrl.replace("http://www.batoto.net/", "http://bato.to/")
		# 		print("Link", sourceUrl)

		# 		cur.execute("SELECT dbId FROM {tableName} WHERE sourceUrl=%s;".format(tableName=self.tableName), (sourceUrl, ))
		# 		ret = cur.fetchall()
		# 		if not ret:
		# 			print("Updating")
		# 			cur.execute("UPDATE {tableName} SET sourceUrl=%s WHERE dbId=%s;".format(tableName=self.tableName), (sourceUrl, dbId))

		# 		else:
		# 			print("Replacing")
		# 			cur.execute("DELETE FROM {tableName} WHERE sourceUrl=%s;".format(tableName=self.tableName), (sourceUrl, ))
		# 			cur.execute("UPDATE {tableName} SET sourceUrl=%s WHERE dbId=%s;".format(tableName=self.tableName), (sourceUrl, dbId))


		cur.execute("COMMIT;")

	def renameDlPaths(self):
		nt.dirNameProxy.startDirObservers()
		cur = self.conn.cursor()
		cur.execute("BEGIN ;")
		cur.execute("SELECT dbId, downloadPath, seriesName FROM mangaitems ORDER BY retreivalTime DESC;")
		rows = cur.fetchall()
		print("Processing %s items" % len(rows))
		cnt = 0
		for row in rows:
			dbId, filePath, seriesName = row
			if filePath == None:
				filePath = ''
			if seriesName == '' or seriesName == None:
				print("No series name", row)
				continue

			if not os.path.exists(filePath):
				if seriesName in nt.dirNameProxy:
					itemPath = nt.dirNameProxy[seriesName]['fqPath']
					if os.path.exists(itemPath):
						print("Need to change", filePath, itemPath)
						cur.execute("UPDATE mangaitems SET downloadPath=%s WHERE dbId=%s", (itemPath, dbId))

			cnt += 1
			if cnt % 1000 == 0:
				print("ON row ", cnt)
				cur.execute("COMMIT;")
				cur.execute("BEGIN;")

		cur.execute("COMMIT;")
		nt.dirNameProxy.stop()

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
		print("	'fix-bt-links' - Fix links for Batoto that point to batoto.com, rather then bato.to.")
		print("	'cross-sync' - Sync name lookup table with seen series.")
		print("	'fix-bad-series' - Consolidate series names to MangaUpdates standard naming.")
		return

	mainArg = sys.argv[1]

	print ("Passed arg", mainArg)


	pc = PathCleaner()
	pc.openDB()

	if mainArg.lower() == "reset-missing":
		pc.resetMissingDownloads()
	elif mainArg.lower() == "clear-bad-dedup":
		pc.clearInvalidDedupTags()
	elif mainArg.lower() == "fix-bt-links":
		pc.patchBatotoLinks()
	elif mainArg.lower() == "cross-sync":
		pc.crossSyncNames()
	elif mainArg.lower() == "fix-bad-series":
		pc.consolidateSeriesNaming()
	elif mainArg.lower() == "fix-dl-paths":
		pc.renameDlPaths()
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

