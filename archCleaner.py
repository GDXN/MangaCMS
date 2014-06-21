


import os
import os.path

import zipfile
import hashlib

import zipfile
import settings
import logging
import magic


# Utility class that scans the contents of a zip archive for any of a number of "bad" files (loaded from settings.badImageDir).
# If it finds any of the bad files in the archive, it re-creates the archive with with the bad file deleted.
class ArchCleaner(object):

	loggerPath = "Main.ZipClean"
	def __init__(self):


		self.log = logging.getLogger(self.loggerPath)

		badIms = os.listdir(settings.badImageDir)

		self.badHashes = []

		for im in badIms:
			with open(os.path.join(settings.badImageDir, im), "rb") as fp:
				md5 = hashlib.md5()
				md5.update(fp.read())
				self.badHashes.append(md5.hexdigest())
				self.log.info("Bad Image = '%s', Hash = '%s'", im, md5.hexdigest())

		# MD5 hashes of the images we want to remove (only one, at the moment)
		# self.badHashes = ['17cfa019168817f3297d3640709c4787']
		# MD5 because cryptographic security is not important here

	# So starkana, in an impressive feat of douchecopterness, inserts an annoying self-promotion image
	# in EVERY manga archive the serve. Furthermore, they insert it in the MIDDLE of the manga.
	# Therefore, this function edits the zip and removes this stupid annoying file.
	def cleanZip(self, zipPath):

		if not os.path.exists(zipPath):
			raise ValueError("Trying to clean non-existant file?")

		if not magic.from_file(zipPath, mime=True).decode("ascii") == 'application/zip':
			raise ValueError("Trying to clean a file that is not a zip archive! File=%s" % zipPath)


		self.log.info("Scanning zip '%s'", zipPath)
		old_zfp = zipfile.ZipFile(zipPath, "r")

		fileNs = old_zfp.infolist()
		files = []
		hadAdvert = False
		for fileInfo in fileNs:

			fctnt = old_zfp.open(fileInfo).read()
			md5 = hashlib.md5()
			md5.update(fctnt)

			# Replace bad image with a text-file with the same name, and an explanation in it.
			if md5.hexdigest() in self.badHashes:
				self.log.info("File %s was the advert. Removing!", fileInfo.filename)
				fileInfo.filename = fileInfo.filename + ".deleted.txt"
				fctnt  = "This was an advertisement. It has been automatically removed.\n"
				fctnt += "Don't worry, there are no missing files, despite the gap in the numbering."

				hadAdvert = True

			files.append((fileInfo, fctnt))

		old_zfp.close()

		# only replace the file if we need to
		if hadAdvert:
			# Now, recreate the zip file without the ad
			self.log.info("Had advert. Rebuilding zip.")
			new_zfp = zipfile.ZipFile(zipPath, "w")
			for fileInfo, contents in files:
				new_zfp.writestr(fileInfo, contents)
			new_zfp.close()
		else:
			self.log.info("No offending contents. No changes made to file.")

if __name__ == "__main__":

	import logSetup
	logSetup.initLogging()

	run = ArchCleaner()

	basePath = '/media/Storage/MP/The Gamer [++++]/'

	for filePath in os.listdir(basePath):
		fqPath = os.path.join(basePath, filePath)
		fType = magic.from_file(fqPath, mime=True).decode("ascii")

		if fType == 'application/zip':
			run.cleanZip(fqPath)

