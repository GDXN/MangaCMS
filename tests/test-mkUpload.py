
import logSetup
if __name__ == "__main__":
	logSetup.initLogging()

import sqlite3

import UploadPlugins.Madokami.uploader as up
import os
import os.path

TESTPATH = "/media/Storage/MP/The Gamer [++++]/"
def test():
	con = up.MkUploader()
	con.checkInitDirs()
	for fileN in os.listdir(TESTPATH):
		fqPath = os.path.join(TESTPATH, fileN)
		con.uploadFile("The Gamer", fqPath)


if __name__ == "__main__":
	test()
