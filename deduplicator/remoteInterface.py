import rpyc
import time

def go():
	x = conn.root.isBinaryUnique()
	print("exiting")


class PCleaner(ScrapePlugins.DbBase.DbBase):
	loggerPath = "Main.DirDedup"
	tableName  = "HentaiItems"

	def __init__(self, scanEnv, removeDir, distance):
		self.conn = rpyc.connect("localhost", 12345)
		self.proc = conn.root.TreeProcessor(scanEnv, removeDir, 3, callBack=self.callBack)
	def callBack(self, delItem, dupItem):
		print("callback")
		print("	", delItem)
		print("	", dupItem)
	def pClean(targetDir):


def pClean(targetDir, removeDir, scanEnv):
	print("Wat", targetDir, removeDir, scanEnv)

	print("Connected.")
	proc = conn.root.TreeProcessor(scanEnv, removeDir, 3, callBack=callBack)
	print("Loaded. Starting scan")
	proc.trimFiles(targetDir)


if __name__ == "__main__":
	go()
