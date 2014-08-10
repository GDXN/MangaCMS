

import ftplib
from settings import mkSettings
import logging
import os
import nameTools as nt

class MkUploader(object):
	log = logging.getLogger("Main.Mk.Uploader")
	def __init__(self):
		self.ftp = ftplib.FTP(host=mkSettings["ftpAddr"])
		self.ftp.login()

		self.haveDirs = {}

	def loadRemoteDirectory(self, fullPath):
		self.haveDirs = {}
		for dirName, stats in self.ftp.mlsd(fullPath):

			# Skip items that aren't directories
			if stats["type"]!="dir":
				continue

			matchingName = nt.getCanonicalMangaUpdatesName(dirName)
			matchingName = nt.prepFilenameForMatching(matchingName)

			if matchingName in self.haveDirs:
				raise ValueError("Duplicate items in directory!")

			self.haveDirs[matchingName] = dirName

	def checkInitDirs(self):
		try:
			dirs = list(self.ftp.mlsd(mkSettings["uploadContainerDir"]))
		except ftplib.error_perm:
			self.log.critical("Container dir for uploads ('%s') does not exist!", mkSettings["uploadContainerDir"])
			raise

		fullPath = os.path.join(mkSettings["uploadContainerDir"], mkSettings["uploadDir"])
		if mkSettings["uploadDir"] not in [item[0] for item in dirs]:
			self.log.info("Need to create base container path")
			self.ftp.mkd(fullPath)
		else:
			self.log.info("Base container directory exists.")

		self.loadRemoteDirectory(fullPath)



	def uploadFile(self, seriesName, filePath):
		seriesName = nt.getCanonicalMangaUpdatesName(seriesName)
		safeSeriesName = nt.makeFilenameSafe(seriesName)
		matchName = nt.prepFilenameForMatching(seriesName)
		if not matchName in self.haveDirs:
			self.log.info("Need to create container directory for %s", seriesName)
			newDir = os.path.join(mkSettings["uploadContainerDir"], mkSettings["uploadDir"], safeSeriesName)
			self.ftp.mkd(newDir)
		else:
			newDir = os.path.join(mkSettings["uploadContainerDir"], mkSettings["uploadDir"], self.haveDirs[matchName])

		dummy_path, filename = os.path.split(filePath)
		self.log.info("Uploading file %s", filePath)
		print("target dir = ", newDir)
		self.ftp.cwd(newDir)
		self.ftp.storbinary("STOR %s" % filename, open(filePath, "rb"))
		self.log.info("File Uploaded")


def uploadFile(seriesName, filePath):
	uploader = MkUploader()
	uploader.checkInitDirs()
	uploader.uploadFile(seriesName, filePath)


def test():
	pass

if __name__ == "__main__":
	test()

