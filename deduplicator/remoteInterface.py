import rpyc
import time
import os.path
import ScrapePlugins.DbBase
import settings

def go():
	x = conn.root.isBinaryUnique()
	print("exiting")


class PCleaner(ScrapePlugins.RetreivalDbBase.ScraperDbBase):
	loggerPath = "Main.DirDedup"
	tableName  = "HentaiItems"

	pluginName = "Cleaner"
	tableKey = None

	QUERY_DEBUG = False


	def __init__(self, scanEnv, removeDir, distance):

		self.remote = rpyc.connect("localhost", 12345)
		self.proc = self.remote.root.TreeProcessor(scanEnv, removeDir, 3, callBack=self.callBack)
		super().__init__()

	def callBack(self, delItem, dupItem):
		self.log.info("callback")

		self.proc.removeArchive(delItem)
		delItemRoot, delItemFile = os.path.split(delItem)
		dupItemRoot, dupItemFile = os.path.split(dupItem)
		self.log.info("	'%s', '%s'" % (delItemRoot, delItemFile))
		self.log.info("	'%s', '%s'" % (dupItemRoot, dupItemFile))

		srcRow = self.getRowsByValue(limitByKey=False, downloadpath=delItemRoot, filename=delItemFile)
		dstRow = self.getRowsByValue(limitByKey=False, downloadpath=dupItemRoot, filename=dupItemFile)

		# print("HaveItem", srcRow)
		if not settings.mangaCmsHContext in dupItemRoot:
			self.log.error("Item not within the context of the relinker")
		else:
			if srcRow and len(srcRow) == 1:
				srcId = srcRow[0]['dbId']
				self.log.info("Relinking!")
				self.updateDbEntryById(srcId, filename=dupItemFile, downloadpath=dupItemRoot)
				self.addTags(dbId=srcId, tags='deleted was-duplicate phash-duplicate')

				if dstRow and len(dstRow) == 1:

					dstId = dstRow[0]['dbId']
					self.addTags(dbId=srcId, tags='crosslink-{dbId}'.format(dbId=srcId))
					self.addTags(dbId=dstId, tags='crosslink-{dbId}'.format(dbId=srcId))
					self.log.info("Found destination row. Cross-linking!")

	def pClean(self, targetDir):
		self.proc.trimFiles(targetDir)

	def go(self):
		pass

def pClean(targetDir, removeDir, scanEnv):
	print("Wat", targetDir, removeDir, scanEnv)

	print("Connected.")
	cleaner = PCleaner(scanEnv, removeDir, 3)

	print("Loaded. Starting scan")
	cleaner.pClean(targetDir)


if __name__ == "__main__":
	go()

