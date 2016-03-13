
import logSetup
if __name__ == "__main__":
	logSetup.initLogging()



import runStatus
runStatus.preloadDicts = False


import UploadPlugins.Madokami.uploader as up
import os
import os.path

TESTPATH = "/media/Storage/Manga/Shirokuma Café/"
def test():
	con = up.MkUploader()
	con.checkInitDirs()

	# con.migrateTempDirContents()

	for fileN in os.listdir(TESTPATH):
		fqPath = os.path.join(TESTPATH, fileN)
		try:
			con.uploadFile("Shirokuma Café", fqPath, db_commit=False)
		except Exception:
			pass


if __name__ == "__main__":
	test()
