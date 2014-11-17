
import rpyc
import time
import os.path
import os
import ScrapePlugins.RetreivalDbBase
import settings

def go():
	x = conn.root.isBinaryUnique()
	print("exiting")


class PCleaner(ScrapePlugins.RetreivalDbBase.ScraperDbBase):
	loggerPath = "Main.DirDedup"
	tableName  = "MangaItems"

	pluginName = "Cleaner"
	tableKey = None

	QUERY_DEBUG = False


	def __init__(self):

		self.remote = rpyc.connect("localhost", 12345)
		self.db = self.remote.root.DbApi()
		super().__init__()

	# def callBack(self, delItem, dupItem):
	# 	self.log.info("callback")

	# 	self.proc.removeArchive(delItem)
	# 	delItemRoot, delItemFile = os.path.split(delItem)
	# 	dupItemRoot, dupItemFile = os.path.split(dupItem)
	# 	self.log.info("Remove:	'%s', '%s'" % (delItemRoot, delItemFile))
	# 	self.log.info("Match: 	'%s', '%s'" % (dupItemRoot, dupItemFile))

	# 	srcRow = self.getRowsByValue(limitByKey=False, downloadpath=delItemRoot, filename=delItemFile)
	# 	dstRow = self.getRowsByValue(limitByKey=False, downloadpath=dupItemRoot, filename=dupItemFile)

	# 	# print("HaveItem", srcRow)
	# 	if not settings.mangaCmsHContext in dupItemRoot:
	# 		self.log.warn("Item not within the context of the relinker. Not fixing database")
	# 	else:
	# 		if srcRow and len(srcRow) == 1:
	# 			srcId = srcRow[0]['dbId']
	# 			self.log.info("Relinking!")
	# 			self.updateDbEntryById(srcId, filename=dupItemFile, downloadpath=dupItemRoot)
	# 			self.addTags(dbId=srcId, tags='deleted was-duplicate phash-duplicate')

	# 			if dstRow and len(dstRow) == 1:

	# 				dstId = dstRow[0]['dbId']
	# 				self.addTags(dbId=srcId, tags='crosslink-{dbId}'.format(dbId=srcId))
	# 				self.addTags(dbId=dstId, tags='crosslink-{dbId}'.format(dbId=srcId))
	# 				self.log.info("Found destination row. Cross-linking!")

	# def pClean(self, targetDir):
	# 	self.proc.trimFiles(targetDir)

	def go(self):
		pass

	def close(self):
		self.remote.close()

def pClean(targetDir, removeDir, scanEnv):
	print("NO LONGER USEABLE")

def treeReload():

	cleaner = PCleaner()
	print("Connected. Forcing reload")
	cleaner.db.forceReload()
	print("Complete")




def iterateClean(targetDir, removeDir):
	items = [os.path.join(targetDir,item) for item in os.listdir(targetDir) if os.path.isdir(os.path.join(targetDir,item))]
	items.sort()
	for item in items:
		print(item)
		cleaner = PCleaner(scanEnv=None, removeDir=removeDir, distance=2)
		cleaner.pClean(item)
		cleaner.close()


