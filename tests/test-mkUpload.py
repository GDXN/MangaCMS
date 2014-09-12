
import logSetup
if __name__ == "__main__":
	logSetup.initLogging()



import runStatus
runStatus.preloadDicts = False


import UploadPlugins.Madokami.uploader as up
import os
import os.path

TESTPATH = "/media/Storage/MP/Koalove [++]/"
def test():
	con = up.MkUploader()
	con.checkInitDirs()

	con.migrateTempDirContents()

	# for fileN in os.listdir(TESTPATH):
	# 	fqPath = os.path.join(TESTPATH, fileN)
	# 	con.uploadFile("Koalove", fqPath)


if __name__ == "__main__":
	test()
