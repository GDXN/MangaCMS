
import rpyc
import time
import os.path
import os
import ScrapePlugins.RetreivalDbBase
import settings

def go():
	x = conn.root.isBinaryUnique()
	print("exiting")


class RemoteInt(ScrapePlugins.RetreivalDbBase.ScraperDbBase):
	loggerPath = "Main.DirDedup"
	tableName  = "MangaItems"

	pluginName = "Cleaner"
	tableKey = None

	QUERY_DEBUG = False


	def __init__(self):

		self.remote = rpyc.connect("localhost", 12345)

		super().__init__()

	def reloadTree(self):
		self.log.warning("Forcing reload of phash tree. Search functionality will block untill load is complete.")
		self.remote.root.reloadTree()
		self.log.warning("Tree reloaded!")

	def go(self):
		pass

	def close(self):
		self.remote.close()




def cleanDirectory(dirPath, delDir):

	import magic
	import processDownload


	print("Processing subdirectory '%s'" % dirPath)
	if not dirPath.endswith("/"):
		dirPath = dirPath + '/'

	items = os.listdir(dirPath)

	items = [os.path.join(dirPath, item) for item in items]

	dirs = [i for i in items if os.path.isdir(i)]
	print("Recursing into %s subdirectories!", len(dirs))
	for subDir in dirs:
		cleanDirectory(subDir, delDir)


	parsedItems = [(os.path.getsize(i), i) for i in items if os.path.isfile(i)]

	parsedItems.sort()


	for dummy_num, basePath in parsedItems:
		print("Item", dummy_num, basePath)


		fType = magic.from_file(basePath, mime=True)

		if fType == 'application/zip' or fType == 'application/x-rar':
			print(basePath)
			processDownload.dedupItem(basePath, delDir)
			# run.processNewArchive(fileP)



def pClean(targetDir, removeDir):
	cleanDirectory(targetDir, removeDir)

	# raise ValueError("Requires size-first sorting!")

	# for root, dirs, files in os.walk(targetDir):
	# 	for name in files:
	# 		fileP = os.path.join(root, name)
	# 		if not os.path.exists(fileP):
	# 			raise ValueError


	print("NO LONGER USEABLE")

def treeReload():

	remote = RemoteInt()
	print("Connected. Forcing reload")
	remote.reloadTree()
	print("Complete")




def iterateClean(targetDir, removeDir):
	items = [os.path.join(targetDir,item) for item in os.listdir(targetDir) if os.path.isdir(os.path.join(targetDir,item))]
	items.sort()
	for item in items:
		print(item)
		cleaner = PCleaner(scanEnv=None, removeDir=removeDir, distance=2)
		cleaner.pClean(item)
		cleaner.close()


