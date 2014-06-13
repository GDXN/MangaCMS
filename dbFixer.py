

import logSetup
logSetup.initLogging()

import time
import traceback
import settings
import sys
import os
import sqlite3
import ScrapePlugins.RetreivalDbBase
import ScrapePlugins.RunBase
import ScrapePlugins.MonitorDbBase


class MangaLinkMigrator(ScrapePlugins.RetreivalDbBase.ScraperDbBase):

	loggerPath = "Main.MangaLinkMigrator"
	pluginName = "MangaLinkMigrator"
	dbName = settings.dbName
	tableName = "MangaItems"


	def __init__(self):
		print("Startomg up")
		super().__init__()

		self.oldDb = sqlite3.connect(settings.oldDbName, timeout=10)

	def go(self):
		print("Migrating Manga DB")
		oCur = self.oldDb.cursor()

		ret = oCur.execute("""SELECT addDate, processing, downloaded, dlName, dlLink, baseName, dlPath, fName, isMp, newDir FROM links;""")

		loops = 0

		rets = ret.fetchall()
		for oldRow in rets:
			# print(addDate, processing, downloaded, dlName, dlLink, seriesName, dlPath, fName, isMp, newDir)
			addDate, processing, downloaded, dlName, dlLink, seriesName, dlPath, fName, isMp, newDir = oldRow
			dlState = 0
			if processing == 1:
				dlState = 1
			if downloaded == 1:
				dlState = 2


			row = self.getRowsByValue(sourceUrl=dlLink)
			if not row:
				self.insertIntoDb(dlState=dlState, sourceUrl=dlLink, retreivalTime=addDate, commit=False)


			flags = []
			if isMp == 1:
				flags.append("picked")
			if newDir == 1:
				flags.append("newdir")

			flags = " ".join(flags)

			self.updateDbEntry(dlLink, originName=dlName, fileName=fName, downloadPath=dlPath, seriesName=seriesName, flags=flags)

			loops += 1
			if loops % 100 == 0:
				print("Loop", loops)

		self.conn.commit()


class FufufuuLinkMigrator(ScrapePlugins.RetreivalDbBase.ScraperDbBase):

	loggerPath = "Main.FufufuuLinkMigrator"
	pluginName = "FufufuuLinkMigrator"
	dbName = settings.dbName
	tableName = "FufufuuItems"


	def __init__(self):
		print("Startomg up")
		super().__init__()

		self.oldDb = sqlite3.connect(settings.oldDbName, timeout=10)

	def go(self):
		print("Migrating Fufufuu DB")
		print(self.tableName)
		oCur = self.oldDb.cursor()

		ret = oCur.execute("""SELECT addDate, processing, downloaded, dlName, dlLink, itemTags, dlPath, fName FROM fufufuu;""")


		loops = 0

		rets = ret.fetchall()
		for addDate, processing, downloaded, dlName, dlLink, itemTags, dlPath, fName in rets:
			# print(addDate, processing, downloaded, dlName, dlLink, seriesName, dlPath, fName, isMp, newDir)

			dlState = 0
			if processing == 1:
				dlState = 1
			if downloaded == 1:
				dlState = 2


			self.insertIntoDb(dlState=dlState, sourceUrl=dlLink, retreivalTime=addDate, commit=False)


			itemTags = itemTags.replace(", ", " ")

			filePath, fileName = os.path.split(dlPath)

			self.updateDbEntry(dlLink, seriesName=dlName, originName=fName, fileName=fileName, downloadPath=filePath, tags=itemTags)

			loops += 1
			if loops % 100 == 0:
				print("Loop", loops)

		self.conn.commit()


class DoujinMoeLinkMigrator(ScrapePlugins.RetreivalDbBase.ScraperDbBase):

	loggerPath = "Main.DoujinMoeLinkMigrator"
	pluginName = "DoujinMoeLinkMigrator"
	dbName = settings.dbName
	tableName = "DoujinMoeItems"


	def __init__(self):
		print("Startomg up")
		super().__init__()

		self.oldDb = sqlite3.connect(settings.oldDbName, timeout=10)

	def go(self):
		print("Migrating Fufufuu DB")
		print(self.tableName)
		oCur = self.oldDb.cursor()

		ret = oCur.execute("""SELECT addDate, processing, downloaded, dlName, contentId, itemTags, dlPath, fName, note FROM djMoe;""")


		loops = 0

		rets = ret.fetchall()
		for addDate, processing, downloaded, dlName, contentId, itemTags, dlPath, fName, note in rets:
			# print(addDate, processing, downloaded, dlName, dlLink, seriesName, dlPath, fName, isMp, newDir)

			dlState = 0
			if processing == 1:
				dlState = 1
			if downloaded == 1:
				dlState = 2


			row = self.getRowsByValue(sourceUrl=contentId)
			if not row:
				self.insertIntoDb(dlState=dlState, sourceUrl=contentId, retreivalTime=addDate, commit=False)


			tags = itemTags.split(",")
			tags = [tag.rstrip().lstrip().replace(" ", "-") for tag in tags]
			itemTags = " ".join(tags)

			if itemTags == "untagged":
				itemTags = None
			filePath, fileName = os.path.split(dlPath)

			self.updateDbEntry(contentId, seriesName=dlName, originName=fName, fileName=fileName, downloadPath=filePath, tags=itemTags, note=note)

			loops += 1
			if loops % 100 == 0:
				print("Loop", loops)

		self.conn.commit()

class StatusTableMigrator(ScrapePlugins.RunBase.ScraperBase):

	loggerPath = "Main.StatusTableMigrator"
	pluginName = "StatusTableMigrator"
	dbName = settings.dbName
	tableName = "pluginStatus"


	def _go(self):

		oldDb = sqlite3.connect(settings.oldDbName, timeout=10)
		con = sqlite3.connect(settings.dbName, timeout=30)
		print("Migrating Fufufuu DB")
		print(self.tableName)
		oCur = oldDb.cursor()

		ret = oCur.execute("""SELECT name, running, lastRun, lastRunTime FROM pluginStatus;""")

		rets = ret.fetchall()
		for name, running, lastRun, lastRunTime in rets:
			con.execute("""INSERT INTO pluginStatus (name, running, lastRun, lastRunTime) VALUES (?, ?, ?, ?);""", (name, running, lastRun, lastRunTime))

		con.commit()

		oldDb.close()
		con.close()

	def closeDB(self):
		pass

class MangaInfoTableMigrator(ScrapePlugins.MonitorDbBase.MonitorDbBase):

	loggerPath = "Main.MangaSeriesMigrator"
	pluginName = "MangaSeriesMigrator"
	dbName = settings.dbName
	tableName = "MangaSeries"


	def __init__(self):
		print("Startomg up")
		super().__init__()

		self.oldDb = sqlite3.connect(settings.oldDbName, timeout=10)
	def go(self):
		pass

if __name__ == "__main__":

	if len(sys.argv) > 1 and sys.argv[1] == "delete":
		print("Deleting and recreating DB")
		if os.path.exists(settings.dbName):
			os.unlink(settings.dbName)

		mlM = MangaLinkMigrator()
		mlM.go()
		mlM.closeDB()

		flM = FufufuuLinkMigrator()
		flM.go()
		flM.closeDB()

		dlM = DoujinMoeLinkMigrator()
		dlM.go()
		dlM.closeDB()

		stM = StatusTableMigrator()
		stM.go()
		stM.closeDB()

	buM = MangaInfoTableMigrator()
	# buM.insertIntoDb(mtName="derp", buName="lol", buId="wat", lastChanged=time.time())
	# print(buM.getRowsByValue(mtName="derp"))
	# print(buM.getRowsByValue(mtName="wat"))
	# print(buM.getRowsByValue(buId="wat"))
	buM.printDb()
	buM.closeDB()
	sys.exit()

