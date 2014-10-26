import rpyc
import time
import os.path
import ScrapePlugins.DbBase

def go():
	x = conn.root.isBinaryUnique()
	print("exiting")


class PCleaner(ScrapePlugins.RetreivalDbBase.ScraperDbBase):
	loggerPath = "Main.DirDedup"
	tableName  = "HentaiItems"

	pluginName = "Cleaner"
	tableKey = None



	def __init__(self, scanEnv, removeDir, distance):

		self.remote = rpyc.connect("localhost", 12345)
		self.proc = self.remote.root.TreeProcessor(scanEnv, removeDir, 3, callBack=self.callBack)
		super().__init__()

	def callBack(self, delItem, dupItem):
		print("callback")
		print("	", delItem)
		print("	", dupItem)

		delItemRoot, delItemFile = os.path.split(delItem)
		dupItemRoot, dupItemFile = os.path.split(dupItem)
		print("'%s', '%s'" % (delItemRoot, delItemFile))
		print("'%s', '%s'" % (dupItemRoot, dupItemFile))

		ret = self.getRowsByValue(limitByKey=False, downloadpath=delItemRoot, filename=delItemFile)
		print("HaveItem", ret)

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

