
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
import Levenshtein as lv
import socket
import ftfy
import traceback

import paramiko

COMPLAIN_ABOUT_DUPS = True

import urllib.parse
import ScrapePlugins.RetreivalDbBase

import stat

class CanonMismatch(Exception):
	pass


def getSftpConnection():

	host = settings.mkSettings["ftpAddr"]
	port = settings.mkSettings["sftpPort"]

	user   = settings.mkSettings["ftpUser"]
	passwd = settings.mkSettings["ftpPass"]

	t = paramiko.Transport((host, port))
	t.connect(None, user, passwd)
	sftp = paramiko.SFTPClient.from_transport(t)
	return sftp


def splitall(path):
	allparts = []
	while 1:
		parts = os.path.split(path)
		if parts[0] == path:  # sentinel for absolute paths
			allparts.insert(0, parts[0])
			break
		elif parts[1] == path: # sentinel for relative paths
			allparts.insert(0, parts[1])
			break
		else:
			path = parts[0]
			allparts.insert(0, parts[1])
	return allparts

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

		self.log.info("Initializing SFTP connection")
		self.sftp = getSftpConnection()
		self.log.info("SFTP connected.")

		self.log.info("Init finished.")
		self.mainDirs     = {}
		self.unsortedDirs = {}


	def go(self):
		pass

	def moveItemsInDir(self, srcDirPath, dstDirPath):
		# FTP is /weird/. Rename apparently really wants to use the cwd for the srcpath param, even if the
		# path starts with "/". Therefore, we have to reset the CWD.
		self.log.info("Source: '%s'", srcDirPath)
		self.log.info("Dest:   '%s'", dstDirPath)
		self.sftp.chdir("/")
		for itemName, dummy_stats in self.sftp.listdir(srcDirPath):
			# itemName = ftfy.fix_text(itemName)
			if itemName == ".." or itemName == ".":
				continue

			srcPath = os.path.join(srcDirPath, itemName)
			try:
				dstPath = os.path.join(dstDirPath, itemName)
				self.sftp.rename(srcPath, dstPath)
			except ftplib.error_perm:
				base, ext = os.path.splitext(itemName)
				dstPath = os.path.join(dstDirPath, base+" (1)"+ext)
				self.sftp.rename(srcPath, dstPath)

			self.log.info("	Moved from '%s'", srcPath)
			self.log.info("	        to '%s'", dstPath)



	def aggregateDirs(self, pathBase_1, pathBase_2, dir1, dir2):
		canonName    = nt.getCanonicalMangaUpdatesName(dir1)
		canonNameAlt = nt.getCanonicalMangaUpdatesName(dir2)
		cname1 = nt.prepFilenameForMatching(canonName)
		cname2 = nt.prepFilenameForMatching(canonNameAlt)
		if canonName.lower() != canonNameAlt.lower():
			self.log.critical("Error in uploading file. Name lookup via MangaUpdates table not commutative!")
			self.log.critical("First returned value    '%s'", canonName)
			self.log.critical("For directory with path '%s'", dir1)
			self.log.critical("Second returned value   '%s'", canonNameAlt)
			self.log.critical("For directory with path '%s'", dir2)
			self.log.critical("After cleaning: '%s', '%s', equal: '%s'", cname1, cname2, cname1 == cname2)


			raise CanonMismatch("Identical and yet not? '%s' - '%s'" % (canonName, canonNameAlt))
		self.log.info("Aggregating directories for canon name '%s':", canonName)

		n1 = lv.distance(dir1, canonName)
		n2 = lv.distance(dir2, canonName)

		self.log.info("	%s - '%s'", n1, dir1)
		self.log.info("	%s - '%s'", n2, dir2)

		# I'm using less then or equal, so situations where
		# both names are equadistant get aggregated anyways.
		if n1 <= n2:
			src = os.path.join(pathBase_2, dir2)
			dst = os.path.join(pathBase_1, dir1)
		else:
			src = os.path.join(pathBase_1, dir1)
			dst = os.path.join(pathBase_2, dir2)


		self.moveItemsInDir(src, dst)
		self.log.info("Removing directory '%s'", src)

		self.sftp.rename(src, "/Admin cleanup/autoclean dirs/garbage dir %s" % src.replace("/", ";").replace(" ", "_"))

		return dst

	def loadRemoteDirectory(self, fullPath, aggregate=False):
		ret = {}
		dirs = self.wg.getpage("https://manga.madokami.al/stupidapi/fakedirs")

		requirePrefix = splitall(fullPath)

		badwords = [
			'Non-English',
			'Oneshots',
			'Raws',
			'Novels',
			'_Doujinshi',
			'AutoUploaded from Assorted Sources',
		]

		rows = [tmp for tmp in
					[splitall(item) for item in
						[item[1:] if item.startswith("./") else item for item in dirs.split("\n")]
					]
				if
					(
							len(tmp) >= len(requirePrefix)
						and
							all([tmp[x] == requirePrefix[x] for x in range(len(requirePrefix))])
						and
							not any([badword in tmp for badword in badwords]))
				]


		print(len(rows))
		for line in rows:
			if len(line) == 6:

				dirName = line[-1]
				if not dirName:
					continue
				canonName = nt.getCanonicalMangaUpdatesName(dirName)
				matchingName = nt.prepFilenameForMatching(canonName)

				# prepFilenameForMatching can result in empty directory names in some cases.
				# Detect that, and don't bother with it if that happened.
				if not matchingName:
					continue
				fqPath   = os.path.join(*line)
				fullPath = os.path.join(*line[:-1])

				if matchingName in ret:
					tmp = ret[matchingName]
					matchpath, matchName = os.path.split(tmp[-1])
					if isinstance(tmp, list):
						tmp = tmp.pop()
					if aggregate:
						try:
							fqPath = self.aggregateDirs(fullPath, matchpath,dirName, matchName)
						except CanonMismatch:
							pass
						except ValueError:
							traceback.print_exc()
						except ftplib.error_perm:
							traceback.print_exc()
					else:
						if COMPLAIN_ABOUT_DUPS:
							self.log.warning("Duplicate directories for series '%s'!", canonName)
							self.log.warning("	'%s/%s'", fullPath, dirName)
							self.log.warning("	'%s/%s'", matchpath, matchName)
					ret[matchingName].append(fqPath)

				else:
					ret[matchingName] = [fqPath]

		return ret


	def checkInitDirs(self):
		try:
			tmp = self.sftp.listdir(settings.mkSettings["uploadContainerDir"])
			dirs = list(tmp)
		except ftplib.error_perm:
			self.log.critical("Container dir for uploads ('%s') does not exist!", settings.mkSettings["uploadContainerDir"])
			raise

		fullPath = os.path.join(settings.mkSettings["uploadContainerDir"], settings.mkSettings["uploadDir"])
		if settings.mkSettings["uploadDir"] not in [item[0] for item in dirs]:
			self.log.info("Need to create base container path")
			self.sftp.mkdir(fullPath)
		else:
			self.log.info("Base container directory exists.")

		# We only reach this point if API-based lookup has failed.
		self.mainDirs     = self.loadRemoteDirectory(settings.mkSettings["mainContainerDir"])
		self.unsortedDirs = list(self.sftp.listdir(settings.mkSettings["uploadContainerDir"]))

		self.log.info("Have %s remote directories in primary dirs on FTP server.", len(self.mainDirs))
		self.log.info("Have %s remote directories in autoupload folder FTP server.", len(self.unsortedDirs))

	def checkInitDoujinDirs(self):
		doujinDir = "_Doujinshi"
		fullPath = os.path.join(settings.mkSettings["uploadContainerDir"], settings.mkSettings["uploadDir"], doujinDir)
		try:
			dirs = list(self.sftp.listdir(fullPath))
		except ftplib.error_perm:
			self.log.critical("Container dir for uploads ('%s') does not exist!", settings.mkSettings["uploadContainerDir"])
			raise


		if os.path.join(settings.mkSettings["uploadDir"], doujinDir) not in [item[0] for item in dirs]:
			self.log.info("Need to create base container path")
			self.sftp.mkdir(fullPath)
		else:
			self.log.info("Base container directory exists.")

		self.unsortedDirs = self.loadRemoteDirectory(fullPath)

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
				self.sftp.rmdir(src)


	def getExistingDir(self, seriesName):

		mId = nt.getMangaUpdatesId(seriesName)
		if not mId:
			return False

		self.log.info("Found mId for %s - %s", mId, seriesName)

		passStr = '%s:%s' % (settings.mkSettings["login"], settings.mkSettings["passWd"])
		authHeader = base64.encodestring(passStr.encode("ascii"))
		authHeader = authHeader.replace(b'\n', b'')
		authHeader = {"Authorization": "Basic %s" % authHeader.decode("ascii")}


		dirInfo = self.wg.getpage("https://manga.madokami.al/api/muid/{mId}".format(mId=mId), addlHeaders = authHeader)

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
			seriesName   = nt.getCanonicalMangaUpdatesName(seriesName)
			safeFilename = nt.makeFilenameSafe(seriesName)
			matchName    = nt.prepFilenameForMatching(seriesName)
			matchName    = matchName.encode('utf-8', 'ignore').decode('utf-8')

			self.checkInitDirs()
			if matchName in self.mainDirs:
				ulDir = self.mainDirs[matchName][0]
			elif seriesName in self.mainDirs:
				ulDir = self.mainDirs[seriesName][0]
			else:

				self.log.info("Need to create container directory for %s", seriesName)
				ulDir = os.path.join(settings.mkSettings["uploadContainerDir"], settings.mkSettings["uploadDir"], safeFilename)
				try:
					self.sftp.mkdir(ulDir)
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
					self.sftp.mkdir(ulDir)
				except ftplib.error_perm:
					self.log.warn("Directory exists?")
					self.log.warn(traceback.format_exc())


		return ulDir

	def uploadFile(self, seriesName, filePath, db_commit=True):

		if '(Doujinshi)' in filePath or 'Doujin}' in filePath:
			self.checkInitDoujinDirs()
			ulDir = self.getDoujinshiUploadDirectory(seriesName)
		else:
			ulDir = self.getUploadDirectory(seriesName)

		while not isinstance(ulDir, str):
			ulDir = ulDir[0]

		dummy_path, filename = os.path.split(filePath)
		self.log.info("Uploading file %s", filePath)
		self.log.info("From series %s", seriesName)

		fqUploadPath = os.path.join(ulDir, filename)
		self.log.info("To container directory %s (%s)", ulDir, fqUploadPath)

		self.sftp.chdir(ulDir)
		self.sftp.put(filePath, fqUploadPath)

		# command = "STOR %s" % filename
		# assert self.ftp.encoding.lower() == "UTF-8".lower()
		# self.ftp.storbinary(command, open(filePath, "rb"))
		self.log.info("File Uploaded")


		dummy_fPath, fName = os.path.split(filePath)
		url = urllib.parse.urljoin("https://manga.madokami.al", urllib.parse.quote(filePath.strip("/")))

		if db_commit:
			self.insertIntoDb(retreivalTime = time.time(),
								sourceUrl   = url,
								originName  = fName,
								dlState     = 3,
								seriesName  = seriesName,
								flags       = '',
								tags="uploaded",
								commit = True)  # Defer commiting changes to speed things up


def do_remote_organize():
	uploader = MkUploader()
	uploader.loadRemoteDirectory("/", aggregate=True)



def uploadFile(seriesName, filePath):
	uploader = MkUploader()
	uploader.uploadFile(seriesName, filePath)


def test():
	uploader = MkUploader()
	# uploader.checkInitDirs()
	# print(uploader.getUploadDirectory('Jitsu wa Watashi wa'))
	# print(uploader.getUploadDirectory('Ouroboros'))
	print(uploader.getUploadDirectory('Infection'))
	# print(uploader.getUploadDirectory('Wish Fulfillment'))
	# uploader.loadRemoteDirectory("/")
	# uploader.loadRemoteDirectory("/Manga")
	# uploader.getExistingDir('87 Clockers')
	uploader.uploadFile('87 Clockers', '/media/Storage/Manga/87 Clockers/87 Clockers - v4 c22 [batoto].zip')


if __name__ == "__main__":

	import utilities.testBase as tb
	with tb.testSetup(startObservers=False):
		test()

