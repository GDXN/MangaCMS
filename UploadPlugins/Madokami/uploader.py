
import runStatus
if __name__ == "__main__":
	runStatus.preloadDicts = False

import ftplib
import settings
import logging
import os
import nameTools as nt
import base64
import json
import time
import webFunctions
import ssl
import socket
import traceback

COMPLAIN_ABOUT_DUPS = True

import urllib.parse
import ScrapePlugins.RetreivalDbBase

import chardet

class TolerantFTP(ftplib.FTP_TLS):

	def retrlines(self, cmd, callback = None):
		"""Retrieve data in line mode.  A new port is created for you.

		Args:
		  cmd: A RETR, LIST, or NLST command.
		  callback: An optional single parameter callable that is called
					for each line with the trailing CRLF stripped.
					[default: print_line()]

		Returns:
		  The response code.

		Tolerant of fucked up encoding issues. All received strings are decoded with
		the encoding detected by chardet if the confidence is > 70%.
		The default encoding is used if the chardet detected encoding lacks
		sufficent confidence.
		"""
		if callback is None:
			callback = ftplib.print_line
		self.sendcmd('TYPE A')

		with self.transfercmd(cmd) as conn, conn.makefile('rb', encoding=None) as fp:
			while 1:
				line = fp.readline(self.maxline + 1)
				guess = chardet.detect(line)

				# print("Line type = ", type(line))
				# print("conn type = ", type(conn))
				# print("Guessed encoding - ", chardet.detect(line))
				# print(line)
				if guess['confidence'] > 0.7:
					line = line.decode(guess['encoding'])
				else:
					line = line.decode(self.encoding)

				if len(line) > self.maxline:
					raise ftplib.Error("got more than %d bytes" % self.maxline)
				if self.debugging > 2:
					print('*retr*', repr(line))
				if not line:
					break
				if line[-2:] == ftplib.CRLF:
					line = line[:-2]
				elif line[-1:] == '\n':
					line = line[:-1]
				callback(line)
			# shutdown ssl layer
			if ftplib._SSLSocket is not None and isinstance(conn, ftplib._SSLSocket):
				conn.unwrap()
		return self.voidresp()

class MkUploader(ScrapePlugins.RetreivalDbBase.ScraperDbBase):
	log = logging.getLogger("Main.Mk.Uploader")

	loggerPath = "Main.Manga.Mk.Up"
	pluginName = "Manga.Madokami Content Retreiver"
	tableKey = "mk"
	dbName = settings.DATABASE_DB_NAME

	tableName = "MangaItems"


	def __init__(self):

		super().__init__()


		self.wg = webFunctions.WebGetRobust(logPath=self.loggerPath+".Web")


		self.ftp = TolerantFTP()
		self.ftp.connect(
				host = settings.mkSettings["ftpAddr"],
				port = settings.mkSettings["ftpPort"],
				)


		self.ftp.login(
				user   = settings.mkSettings["ftpUser"],
				passwd = settings.mkSettings["ftpPass"],
				)

		self.ftp.prot_p()
		self.ftp.set_pasv(True)
		self.enableUtf8()
		# print(self.ftp.retrlines('LIST'))

		self.log.info("Init finished.")
		self.mainDirs     = {}
		self.unsortedDirs = {}

	def enableUtf8(self):
		features_string_ftp = self.ftp.sendcmd('FEAT')
		# self.log.info("FTP Feature string: '%s'", features_string_ftp)
		if 'UTF8' in features_string_ftp.upper():
			self.log.info("Server supports UTF-8 charset. Trying to enable it.")
			# Command:	OPTS UTF8 ON
			# Response:	200 UTF8 set to on
			ret = self.ftp.sendcmd('OPTS UTF8 ON')
			self.log.info("Response to 'OPTS UTF8 ON': '%s'", ret)
			ret = ret.upper()
			if "UTF8" in ret and "ON" in ret:
				# Override undocumented class member to set the FTP encoding.
				# This is a HORRIBLE hack.
				self.log.info("FTP Connection set to UTF-8 mode!")
				self.ftp.encoding = "UTF-8"
			else:
				self.log.warn("Could not enable UTF-8 mode?")
		else:
			self.log.warn("Server does not support UTF-8. Some transfers may be broken.")

	def go(self):
		pass

	def moveItemsInDir(self, srcDirPath, dstDirPath):
		# FTP is /weird/. Rename apparently really wants to use the cwd for the srcpath param, even if the
		# path starts with "/". Therefore, we have to reset the CWD.
		self.ftp.cwd("/")
		for itemName, dummy_stats in self.ftp.mlsd(srcDirPath):
			if itemName == ".." or itemName == ".":
				continue
			srcPath = os.path.join(srcDirPath, itemName)
			dstPath = os.path.join(dstDirPath, itemName)
			self.ftp.rename(srcPath, dstPath)
			self.log.info("	Moved from '%s'", srcPath)
			self.log.info("	        to '%s'", dstPath)


	def aggregateDirs(self, pathBase, dir1, dir2):
		canonName = nt.getCanonicalMangaUpdatesName(dir1)
		canonNameAlt = nt.getCanonicalMangaUpdatesName(dir2)
		if canonName != canonNameAlt:
			self.log.critical("Error in uploading file. Name lookup via MangaUpdates table not commutative!")
			self.log.critical("First returned value    '%s'", canonName)
			self.log.critical("For directory with path '%s'", dir1)
			self.log.critical("Second returned value   '%s'", canonNameAlt)
			self.log.critical("For directory with path '%s'", dir2)

			raise ValueError("Identical and yet not?")
		self.log.info("Aggregating directories for canon name '%s':", canonName)

		n1 = lv.distance(dir1, canonName)
		n2 = lv.distance(dir2, canonName)

		self.log.info("	%s - '%s'", n1, dir1)
		self.log.info("	%s - '%s'", n2, dir2)

		# I'm using less then or equal, so situations where
		# both names are equadistant get aggregated anyways.
		if n1 <= n2:
			src = dir2
			dst = dir1
		else:
			src = dir1
			dst = dir2

		src = os.path.join(pathBase, src)
		dst = os.path.join(pathBase, dst)

		self.moveItemsInDir(src, dst)
		self.log.info("Removing directory '%s'", src)
		self.ftp.rmd(src)

		return dst

	def loadRemoteDirectory(self, fullPath, aggregate=False):
		ret = {}

		for dirName, stats in self.ftp.mlsd(fullPath):

			# Skip items that aren't directories
			if stats["type"]!="dir":
				continue

			canonName = nt.getCanonicalMangaUpdatesName(dirName)
			matchingName = nt.prepFilenameForMatching(canonName)

			fqPath = os.path.join(fullPath, dirName)

			# matchName = os.path.split(ret[matchingName])[-1]

			if matchingName in ret:
				# if aggregate:
				# 	fqPath = self.aggregateDirs(fullPath, dirName, matchName)
				# else:
				if COMPLAIN_ABOUT_DUPS:
					self.log.warning("Duplicate directories for series '%s'!", canonName)
					self.log.warning("	'%s'", dirName)
					self.log.warning("	'%s'", matchingName)
				ret[matchingName] = fqPath

			else:
				ret[matchingName] = fqPath

		return ret

	def loadMainDirs(self):
		ret = {}
		try:
			dirs = list(self.ftp.mlsd(settings.mkSettings["mainContainerDir"]))
		except ftplib.error_perm:
			self.log.critical("Container dir ('%s') does not exist!", settings.mkSettings["mainContainerDir"])
		for dirPath, dummy_stats in dirs:
			if dirPath == ".." or dirPath == ".":
				continue
			dirPath = os.path.join(settings.mkSettings["mainContainerDir"], dirPath)
			items = self.loadRemoteDirectory(dirPath)
			for key, value in items.items():
				if key not in ret:
					ret[key] = value
				else:
					for item in value:
						ret[key].append(item)

			self.log.info("Loading contents of FTP dir '%s'.", dirPath)
		self.log.info("Have '%s remote directories on FTP server.", len(ret))
		return ret

	def checkInitDirs(self):
		try:
			tmp = self.ftp.mlsd(settings.mkSettings["uploadContainerDir"])
			dirs = list(tmp)
		except ftplib.error_perm:
			self.log.critical("Container dir for uploads ('%s') does not exist!", settings.mkSettings["uploadContainerDir"])
			raise

		fullPath = os.path.join(settings.mkSettings["uploadContainerDir"], settings.mkSettings["uploadDir"])
		if settings.mkSettings["uploadDir"] not in [item[0] for item in dirs]:
			self.log.info("Need to create base container path")
			self.ftp.mkd(fullPath)
		else:
			self.log.info("Base container directory exists.")



	def checkInitDoujinDirs(self):
		doujinDir = "_Doujinshi"
		fullPath = os.path.join(settings.mkSettings["uploadContainerDir"], settings.mkSettings["uploadDir"], doujinDir)
		try:
			dirs = list(self.ftp.mlsd(fullPath))
		except ftplib.error_perm:
			self.log.critical("Container dir for uploads ('%s') does not exist!", settings.mkSettings["uploadContainerDir"])
			raise


		if os.path.join(settings.mkSettings["uploadDir"], doujinDir) not in [item[0] for item in dirs]:
			self.log.info("Need to create base container path")
			self.ftp.mkd(fullPath)
		else:
			self.log.info("Base container directory exists.")

		# self.mainDirs     = self.loadMainDirs()
		self.unsortedDirs = self.loadRemoteDirectory(fullPath, aggregate=True)


	def migrateTempDirContents(self):
		for key in self.unsortedDirs.keys():
			if key in self.mainDirs and len(self.mainDirs[key]) == 1:
				print("Should move", key)
				print("	Src:", self.unsortedDirs[key])
				print("	Dst:", self.mainDirs[key][0])
				src = self.unsortedDirs[key]
				dst = self.mainDirs[key][0]

				self.moveItemsInDir(src, dst)
				self.log.info("Removing directory '%s'", src)
				self.ftp.rmd(src)


	def getExistingDir(self, seriesName):

		mId = nt.getMangaUpdatesId(seriesName)
		if not mId:
			return False

		self.log.info("Found mId for %s - %s", mId, seriesName)

		passStr = '%s:%s' % (settings.mkSettings["login"], settings.mkSettings["passWd"])
		authHeader = base64.encodestring(passStr.encode("ascii"))
		authHeader = authHeader.replace(b'\n', b'')
		authHeader = {"Authorization": "Basic %s" % authHeader.decode("ascii")}


		dirInfo = self.wg.getpage("https://manga.madokami.com/api/muid/{mId}".format(mId=mId), addlHeaders = authHeader)

		ret = json.loads(dirInfo)
		if not 'result' in ret or not ret['result']:
			self.log.info("No directory information in returned query.")
			return False

		self.log.info("Have directory info from API query. Contains %s directories.", len(ret['data']))
		if len(ret['data']) == 0:
			return False

		dirInfo = ret['data'].pop()
		return dirInfo['path']

	def getUploadDirectory(self, seriesName):

		ulDir = self.getExistingDir(seriesName)

		if not ulDir:
			seriesName = nt.getCanonicalMangaUpdatesName(seriesName)
			safeFilename = nt.makeFilenameSafe(seriesName)
			matchName = nt.prepFilenameForMatching(seriesName)
			matchName = matchName.encode('latin-1', 'ignore').decode('latin-1')

			self.checkInitDirs()
			if matchName in self.unsortedDirs:
				ulDir = self.unsortedDirs[matchName]
			elif safeFilename in self.unsortedDirs:
				ulDir = self.unsortedDirs[safeFilename]
			else:

				self.log.info("Need to create container directory for %s", seriesName)
				ulDir = os.path.join(settings.mkSettings["uploadContainerDir"], settings.mkSettings["uploadDir"], safeFilename)
				try:
					self.ftp.mkd(ulDir)
				except ftplib.error_perm as e:
					# If the error is just a "directory exists" warning, ignore it silently
					if str(e).startswith("550") and str(e).endswith('File exists'):
						pass
					else:
						self.log.warn("Error creating directory?")
						self.log.warn(traceback.format_exc())


		return ulDir

	def getDoujinshiUploadDirectory(self, seriesName):
		ulDir = self.getExistingDir(seriesName)

		if not ulDir:
			seriesName = nt.getCanonicalMangaUpdatesName(seriesName)
			safeFilename = nt.makeFilenameSafe(seriesName)
			matchName = nt.prepFilenameForMatching(seriesName)
			matchName = matchName.encode('latin-1', 'ignore').decode('latin-1')

			self.checkInitDirs()
			if matchName in self.unsortedDirs:
				ulDir = self.unsortedDirs[matchName]
			elif safeFilename in self.unsortedDirs:
				ulDir = self.unsortedDirs[safeFilename]
			else:

				self.log.info("Need to create container directory for %s", seriesName)
				ulDir = os.path.join(settings.mkSettings["uploadContainerDir"], settings.mkSettings["uploadDir"], safeFilename)
				try:
					self.ftp.mkd(ulDir)
				except ftplib.error_perm:
					self.log.warn("Directory exists?")
					self.log.warn(traceback.format_exc())


		return ulDir

	def uploadFile(self, seriesName, filePath):

		if '(Doujinshi)' in filePath or 'Doujin}' in filePath:
			self.checkInitDoujinDirs()
			ulDir = self.getDoujinshiUploadDirectory(seriesName)
		else:
			ulDir = self.getUploadDirectory(seriesName)


		dummy_path, filename = os.path.split(filePath)
		self.log.info("Uploading file %s", filePath)
		self.log.info("From series %s", seriesName)
		self.log.info("To container directory %s", ulDir)
		self.ftp.cwd(ulDir)

		command = "STOR %s" % "test-"+filename

		self.ftp.storbinary(command, open(filePath, "rb"))
		self.log.info("File Uploaded")


		dummy_fPath, fName = os.path.split(filePath)
		url = urllib.parse.urljoin("http://manga.madokami.com", urllib.parse.quote(filePath.strip("/")))

		self.insertIntoDb(retreivalTime = time.time(),
							sourceUrl   = url,
							originName  = fName,
							dlState     = 3,
							seriesName  = seriesName,
							flags       = '',
							tags="uploaded",
							commit = True)  # Defer commiting changes to speed things up





def uploadFile(seriesName, filePath):
	uploader = MkUploader()
	uploader.uploadFile(seriesName, filePath)


def test():
	uploader = MkUploader()
	uploader.checkInitDirs()
	uploader.getExistingDir('87 Clockers')
	uploader.uploadFile('87 Clockers', '/media/Storage/Manga/87 Clockers/87 Clockers - v4 c21 [batoto].zip')


if __name__ == "__main__":

	import utilities.testBase as tb
	with tb.testSetup(startObservers=False):
		test()

