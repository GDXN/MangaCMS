import sys
sys.path.insert(0,"..")
import os.path

import logSetup
if __name__ == "__main__":
	logSetup.initLogging()

import shutil
import ScrapePlugins.DbBase
import rpyc
import os
import nameTools as nt

from utilities.askUser import query_response, query_response_bool

class DirDeduper(ScrapePlugins.DbBase.DbBase):
	loggerPath = "Main.DirDedup"
	tableName  = "MangaItems"


	def setupDbApi(self):

		remote = rpyc.connect("localhost", 12345)
		self.db = remote.root.DbApi()


	def scanSingleDir(self, dirPath):
		print("Dir", dirPath)
		items = os.listdir(dirPath)
		items.sort()
		for item in items:
			item = os.path.join(dirPath, item)
			if os.path.isfile(item):
				fPath, fName = os.path.split(item)
				guessName = nt.guessSeriesFromFilename(fName)

				dirName = fPath.strip("/").split("/")[-1]
				guess2 = nt.guessSeriesFromFilename(dirName)
				if guessName != guess2:
					print("Dirname not matching either?", dirName, guessName)

				if guessName in nt.dirNameProxy:
					itemInfo = nt.dirNameProxy[guessName]
					if itemInfo["fqPath"] != dirPath:
						dstDir = nt.dirNameProxy[guessName]["fqPath"]
						print("Move file '%s' from:" % fName)

						print("	Src = '%s'" % fPath)
						print("	Dst = '%s'" % dstDir)
						doMove = query_response_bool("Do move?")
						if doMove:
							shutil.move(item, os.path.join(dstDir, fName))


	def scanDirectory(self, dirPath):

		self.log.info("Cleaning path '%s'", dirPath)
		items = os.listdir(dirPath)
		items.sort()
		for item in items:
			item = os.path.join(dirPath, item)
			if os.path.isdir(item):
				self.scanSingleDir(item)


def scanDirectories(basePath):

	nt.dirNameProxy.startDirObservers(useObservers=False)
	dd = DirDeduper()
	dd.openDB()
	dd.setupDbApi()

	dd.scanDirectory(basePath)
	dd.closeDB()
