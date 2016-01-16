import sys
sys.path.insert(0,"..")
import os.path

import logSetup
if __name__ == "__main__":
	logSetup.initLogging()

import shutil
import ScrapePlugins.DbBase
import os
import nameTools as nt
import processDownload
from concurrent.futures import ThreadPoolExecutor

class ItemImporter(ScrapePlugins.DbBase.DbBase):
	loggerPath = "Main.ItemImporter"
	tableName  = "MangaItems"



	def scanSingleDir(self, dirPath):
		self.log.info("Dir %s", dirPath)
		items = os.listdir(dirPath)
		items.sort()
		for item in items:
			item = os.path.join(dirPath, item)
			if os.path.isfile(item):
				fPath, fName = os.path.split(item)
				guessName = nt.guessSeriesFromFilename(fName)

				# dirName = fPath.strip("/").split("/")[-1]
				# guess2 = nt.guessSeriesFromFilename(dirName)
				# if guessName != guess2:
				# 	print("Dirname not matching either?", dirName, guessName)

				if guessName in nt.dirNameProxy and nt.dirNameProxy[guessName]["fqPath"]:
					itemInfo = nt.dirNameProxy[guessName]
					# print(itemInfo)
					if itemInfo["fqPath"] != dirPath:
						dstDir = itemInfo["fqPath"]
						print("Move file '%s' from:" % fName)

						print("	Src = '%s'" % fPath)
						print("	Dst = '%s'" % dstDir)

						dstPath = os.path.join(dstDir, fName)

						try:
							shutil.move(item, dstPath)

							# Set pron to True, to prevent accidental uploading.
							processDownload.processDownload(guessName, dstPath, deleteDups=True, includePHash=True, pron=True, crossReference=False)

						except KeyboardInterrupt:
							shutil.move(dstPath, item)
							raise


	def importFromDirectory(self, dirPath):

		self.log.info("Importing from path '%s'", dirPath)
		items = os.listdir(dirPath)
		items.sort()

		with ThreadPoolExecutor(max_workers=4) as tpe:
			for item in items:
				item = os.path.join(dirPath, item)
				if os.path.isdir(item):
					tpe.submit(self.scanSingleDir, item)
					# self.scanSingleDir(item)


def importDirectories(basePath):

	nt.dirNameProxy.startDirObservers(useObservers=False)
	nt.dirNameProxy.refresh()

	dd = ItemImporter()
	# dd.openDB()
	# dd.setupDbApi()

	dd.importFromDirectory(basePath)
	# dd.closeDB()
