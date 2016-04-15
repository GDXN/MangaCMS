

# Ideally, all downloaded archives should run through this function.
import UploadPlugins.Madokami.uploader as up
import archCleaner as ac
import deduplicator.archChecker
import traceback
import os.path
import ScrapePlugins.RetreivalDbBase
import settings
import runStatus

PHASH_DISTANCE = 4


class DownloadProcessor(ScrapePlugins.RetreivalDbBase.ScraperDbBase):

	pluginName = 'Download Processor'

	loggerPath = 'Main.DlProc'
	tableKey = 'n/a'


	def updatePath(self, oldPath, newPath):
		oldItemRoot, oldItemFile = os.path.split(oldPath)
		newItemRoot, newItemFile = os.path.split(newPath)

		srcRow = self.getRowsByValue(limitByKey=False, downloadpath=oldItemRoot, filename=oldItemFile)
		if srcRow and len(srcRow) == 1:
			self.log.info("OldPath:	'%s', '%s'", oldItemRoot, oldItemFile)
			self.log.info("NewPath:	'%s', '%s'", newItemRoot, newItemFile)

			srcId = srcRow[0]['dbId']
			self.log.info("Fixing DB Path!")
			self.updateDbEntryById(srcId, filename=newItemRoot, downloadpath=newItemFile)



	def crossLink(self, delItem, dupItem, isPhash=False):
		self.log.warning("Duplicate found! Cross-referencing file")

		delItemRoot, delItemFile = os.path.split(delItem)
		dupItemRoot, dupItemFile = os.path.split(dupItem)
		self.log.info("Remove:	'%s', '%s'", delItemRoot, delItemFile)
		self.log.info("Match: 	'%s', '%s'", dupItemRoot, dupItemFile)

		srcRow = self.getRowsByValue(limitByKey=False, downloadpath=delItemRoot, filename=delItemFile)
		dstRow = self.getRowsByValue(limitByKey=False, downloadpath=dupItemRoot, filename=dupItemFile)

		# print("HaveItem", srcRow)
		if srcRow and len(srcRow) == 1:
			srcId = srcRow[0]['dbId']
			self.log.info("Relinking!")
			self.updateDbEntryById(srcId, filename=dupItemFile, downloadpath=dupItemRoot)

			if isPhash:
				tags = 'deleted was-duplicate phash-duplicate'
			else:
				tags = 'deleted was-duplicate'

			self.addTags(dbId=srcId, tags=tags, limitByKey=False)

			# Allow for situations where we're linking to something that already has other links
			if dstRow:

				dstId = dstRow[0]['dbId']
				self.addTags(dbId=srcId, tags='crosslink-{dbId}'.format(dbId=dstId), limitByKey=False)
				self.addTags(dbId=dstId, tags='crosslink-{dbId}'.format(dbId=dstId), limitByKey=False)
				self.log.info("Found destination row. Cross-linking!")
				return

		self.log.warn("Cross-referencing file failed!")
		self.log.warn("Remove:	'%s', '%s'", delItemRoot, delItemFile)
		self.log.warn("Match: 	'%s', '%s'", dupItemRoot, dupItemFile)
		self.log.warn("SrcRow:	'%s'", srcRow)
		self.log.warn("DstRow:	'%s'", dstRow)

	def scanIntersectingArchives(self, containerPath, intersections, phashThresh, moveToPath):

		pathFilter = [item['dir'] for item in settings.mangaFolders.values()]
		self.log.info("File intersections:")
		keys = list(intersections)
		keys.sort()
		# Only look at the 3 largest keys
		for key in keys[-2:]:
			if not runStatus.run:
				self.log.warning("Exiting early from scanIntersectingArchives() due to halt flag.")
				return

			self.log.info("	%s common files:", key)

			# And limit the key checks to two files
			for archivePath in intersections[key][:2]:

				# Limit the checked files to just the context of the new file
				if not archivePath.startswith(containerPath):
					continue
				self.log.info("		Scanning %s", archivePath)

				# I need some sort of deletion lock for file removal. Outside deletion is disabled until that's done.
				# EDIT: Wrapped the deduper end in a lock.

				dc = deduplicator.archChecker.ArchChecker(archivePath, phashDistance=phashThresh, pathFilter=pathFilter)
				retTags, bestMatch, dummy_intersections = dc.process(moveToPath=moveToPath)
				retTags = retTags.strip()

				if bestMatch:
					self.log.info("			Scan return: '%s', best-match: '%s'", retTags, bestMatch)
					isPhash = False
					if "phash-duplicate" in retTags:
						isPhash = True
					self.crossLink(archivePath, bestMatch, isPhash=isPhash)
				else:
					self.log.info("			Scan return: '%s'. No best match.", retTags)



	def processDownload(self, seriesName, archivePath, deleteDups=False, includePHash=False, pathFilter=None, crossReference=True, doUpload=True, **kwargs):

		if 'phashThresh' in kwargs:
			phashThresh = kwargs.pop('phashThresh')
			self.log.warn("Phash search distance overridden!")
			self.log.warn("Search distance = %s", phashThresh)
			for line in traceback.format_stack():
				self.log.warn(line.rstrip())

		else:
			phashThresh = PHASH_DISTANCE
			self.log.info("Phash search distance = %s", phashThresh)

		if 'dedupMove' in kwargs:
			moveToPath = kwargs.pop('dedupMove')
		else:
			moveToPath = False

		if moveToPath:
			retTags = ""
		else:
			archCleaner = ac.ArchCleaner()
			try:
				retTags, archivePath = archCleaner.processNewArchive(archivePath, **kwargs)
			except Exception:
				self.log.critical("Error processing archive '%s'", archivePath)
				self.log.critical(traceback.format_exc())
				retTags = "corrupt unprocessable"



		# Limit dedup matches to the served directories.
		if not pathFilter:
			pathFilter = [item['dir'] for item in settings.mangaFolders.values()]

		# Let the remote deduper do it's thing.
		# It will delete duplicates automatically.
		dc = deduplicator.archChecker.ArchChecker(archivePath, phashDistance=phashThresh, pathFilter=pathFilter, lock=False)
		retTagsTmp, bestMatch, intersections = dc.process(moveToPath=moveToPath)
		retTags += " " + retTagsTmp
		retTags = retTags.strip()

		if bestMatch and crossReference:
			isPhash = False
			if "phash-duplicate" in retTags:
				isPhash = True
			self.crossLink(archivePath, bestMatch, isPhash=isPhash)


		# try:
		# 	self.scanIntersectingArchives(os.path.split(archivePath)[0], intersections, phashThresh, moveToPath)
		# except Exception:
		# 	self.log.error("Failure in scanIntersectingArchives()?")
		# 	for line in traceback.format_exc().split("\n"):
		# 		self.log.error(line)
		# 	self.log.error("Ignoring exception")


		# processNewArchive returns "damaged" or "duplicate" for the corresponding archive states.
		# Since we don't want to upload archives that are either, we skip if retTags is anything other then ""
		# Also, don't upload porn
		if (not self.pron) and (not retTags or retTags=="fewfiles") and seriesName and doUpload:
			try:
				self.log.info("Trying to upload file '%s'.", archivePath)
				up.uploadFile(seriesName, archivePath)
				retTags += " uploaded"
			except ConnectionRefusedError:
				self.log.warning("Uploading file failed! Connection Refused!")
			except Exception:
				self.log.error("Uploading file failed! Unknown Error!")
				self.log.error(traceback.format_exc())
		else:
			self.log.info("File not slated for upload: '%s' (tags: '%s')", archivePath, retTags)

		if retTags:
			self.log.info("Applying tags to archive: '%s'", retTags)
		if "deleted" in retTags:
			self.log.warning("Item was deleted!")
		return retTags.strip()


# Subclasses to specify the right table names
class MangaProcessor(DownloadProcessor):
	tableName = 'MangaItems'
	pron = False

class HentaiProcessor(DownloadProcessor):
	tableName = 'HentaiItems'
	pron = True


def processDownload(*args, **kwargs):
	if 'pron' in kwargs:
		isPron = kwargs.pop('pron')
	else:
		isPron = False

	if isPron:
		dlProc = HentaiProcessor()
	else:
		dlProc = MangaProcessor()

	return dlProc.processDownload(*args, **kwargs)

def dedupItem(itemPath, rmPath):
	dlProc = MangaProcessor()
	dlProc.processDownload(seriesName=None, archivePath=itemPath, dedupMove=rmPath, deleteDups=True, includePHash=True)


if __name__ == "__main__":

	import logSetup
	logSetup.initLogging()

	import sys

	if len(sys.argv) > 1:
		processDownload(seriesName=None, archivePath=[sys.argv[1]])

