


import os
import os.path

import hashlib
import settings
import logging
import magic
import UniversalArchiveReader

try:
	import pyximport
	pyximport.install()
	import czipfile.czipfile as zipfile

except ImportError:
	print("Unzipping performance can be increased MASSIVELY by")
	print("installing cython, which will result in the use of a ")
	print("cythonized unzipping package, rather then the (default)")
	print("pure-python zip decyption. ")
	print("")
	print("The speedup achieved via cython can reach ~100x faster then ")
	print("the pure-python implementation~")
	import traceback
	traceback.print_exc()

	print("Falling back to the pure-python implementation due to the lack of cython.")

	import zipfile



try:
	import deduplicator.dupCheck as deduper
	print("Have file deduplication interface. Doing download duplicate checking!")
except:
	deduper = None
	print("No deduplication tools installed.")



# Utility class for common archive cleaning and manipulation tasks.

# `cleanZip()` scans the contents of a archive for any of a number of "bad" files (loaded from settings.badImageDir).
# If it finds any of the bad files in the archive, it re-creates the archive with with the bad file deleted.
# MD5 is used for haching, because cryptographic security is not important here.
# If `cleanZip` is passed a rar file, and it finds files it wants to delete in said rar, it will
# convert the rar to a zip

# `unprotectZip()` removes password-based encryption from a zip file

# `processNewArchive()` takes an archive, and passes it through `cleanZip()` and `unprotectZip()`, and then
# checks it to see if it's duplicated by other files aready in the database.
# It should eventually add it to the database if it's new, or delete it if it's redundant.
# (WIP)

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


	# So starkana, in an impressive feat of douchecopterness, inserts an annoying self-promotion image
	# in EVERY manga archive the serve. Furthermore, they insert it in the MIDDLE of the manga.
	# Therefore, this function edits the zip and removes this stupid annoying file.
	def cleanZip(self, archPath):

		origPath = archPath

		if not os.path.exists(archPath):
			raise ValueError("Trying to clean non-existant file?")

		if not magic.from_file(archPath, mime=True).decode("ascii") == 'application/zip' and \
		   not magic.from_file(archPath, mime=True).decode("ascii") == 'application/x-rar':
			raise ValueError("Trying to clean a file that is not a zip/rar archive! File=%s" % archPath)


		self.log.info("Scanning arch '%s'", archPath)
		old_zfp = UniversalArchiveReader.ArchiveReader(archPath)



		files = []
		hadBadFile = False
		for fileN, fileCtnt in old_zfp:

			if fileN.endswith("Thumbs.db"):
				hadBadFile = True
				self.log.info("Had windows 'Thumbs.db' file. Removing")
				continue

			fctnt = fileCtnt.read()
			md5 = hashlib.md5()
			md5.update(fctnt)

			# Replace bad image with a text-file with the same name, and an explanation in it.
			if md5.hexdigest() in self.badHashes:
				self.log.info("File %s was the advert. Removing!", fileN)
				fileN = fileN + ".deleted.txt"
				fctnt  = "This was an advertisement. It has been automatically removed.\n"
				fctnt += "Don't worry, there are no missing files, despite the gap in the numbering."

				hadBadFile = True

			files.append((fileN, fctnt))

		old_zfp.close()

		# only replace the file if we need to
		if hadBadFile:
			# Now, recreate the zip file without the ad
			self.log.info("Had advert. Rebuilding zip.")
			if archPath.endswith(".rar") or archPath.endswith(".cbr"):
				archPath = archPath.rsplit(".", 1)[0]
				archPath += ".zip"

			new_zfp = zipfile.ZipFile(archPath, "w")
			for fileInfo, contents in files:
				new_zfp.writestr(fileInfo, contents)
			new_zfp.close()

			if origPath != archPath:
				os.remove(origPath)

		else:
			self.log.info("No offending contents. No changes made to file.")

		return archPath


	# Rebuild zipfile `zipPath` that has a password as a non-password protected zip
	# Pre-emptively checks if the zip is really password-protected, and does not
	# rebuild zips that are not password protected.
	def unprotectZip(self, zipPath, password):
		password = password.encode("ascii")
		try:
			old_zfp = zipfile.ZipFile(zipPath, "r")
			files = old_zfp.infolist()
			for fileN in files:
				old_zfp.open(fileN).read()
			self.log.info("Do not need to decrypt zip")
			return

		except RuntimeError:
			pass

		self.log.info("Removing password from zip '%s'", zipPath)
		old_zfp = zipfile.ZipFile(zipPath, "r")
		old_zfp.setpassword(password)
		fileNs = old_zfp.namelist()
		files = []


		# The zip decryption is STUPID slow. It's really insane how shitty
		# the python integrated library is.
		# See czipfile.pyd for some work on making it faster.
		for fileInfo in fileNs:

			fctnt = old_zfp.open(fileInfo).read()
			files.append((fileInfo, fctnt))

		old_zfp.close()

		os.remove(zipPath)

		# only replace the file if we need to
		# Now, recreate the zip file without the ad
		self.log.info("Rebuilding zip without password.")

		new_zfp = zipfile.ZipFile(zipPath, "w")
		for fileInfo, contents in files:
			new_zfp.writestr(fileInfo, contents)
		new_zfp.close()


	def processNewArchive(self, archPath, passwd=""):
		if magic.from_file(archPath, mime=True).decode("ascii") == 'application/zip':
			self.unprotectZip(archPath, passwd)
		elif magic.from_file(archPath, mime=True).decode("ascii") == 'application/x-rar':
			pass
		else:
			self.log.error("ArchCleaner called on file that isn't a rar or zip!")
			self.log.error("Called on file %s", archPath)
			self.log.error("Specified password '%s'", passwd)
			self.log.error("Inferred file type %s", magic.from_file(archPath, mime=True).decode("ascii"))
			raise ValueError("ArchCleaner called on file that isn't a rar or zip!")

		# ArchPath will convert from rar to zip if needed, and returns the name of the resulting
		# file in either case
		archPath = self.cleanZip(archPath)

		if deduper:

			dc = deduper.ArchChecker(archPath)
			isUnique = dc.check()
			if not isUnique:
				self.log.warning("Archive %s isn't unique!" % archPath)
				dc.deleteArch()
			else:
				self.log.info("Archive Contains unique files. Leaving alone!")



if __name__ == "__main__":

	import logSetup
	logSetup.initLogging()

	run = ArchCleaner()

	basePath = '/media/Storage/Manga/'

	for root, dirs, files in os.walk(basePath):
		for name in files:
			fileP = os.path.join(root, name)
			if not os.path.exists(fileP):
				raise ValueError
			fType = magic.from_file(fileP, mime=True).decode("ascii")

			if fType == 'application/zip' or fType == 'application/x-rar':
				run.processNewArchive(fileP)

