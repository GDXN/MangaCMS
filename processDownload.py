

# Ideally, all downloaded archives should run through this function.
import UploadPlugins.Madokami.uploader as up
import archCleaner as ac
import logging
import traceback
import os.path
import ScrapePlugins.RetreivalDbBase


PHASH_DISTANCE = 2


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
		self.log.info("Cross-referencing file")

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


	def processDownload(self, seriesName, archivePath, deleteDups=False, includePHash=False, **kwargs):

		if 'phashThresh' in kwargs:
			phashThresh = kwargs.pop('phashThresh')
		else:
			phashThresh = PHASH_DISTANCE

		try:
			import deduplicator.archChecker

			deduper = True
			print("Have file deduplication interface. Doing download duplicate checking!")
		except:
			deduper = None
			print("No deduplication tools installed.")


		log = logging.getLogger("Main.ArchProc")

		archCleaner = ac.ArchCleaner()
		try:
			retTags, archivePath = archCleaner.processNewArchive(archivePath, **kwargs)
		except:
			self.log.critical("Error processing archive '%s'", archivePath)
			self.log.critical(traceback.format_exc())
			retTags = "corrupt unprocessable"


		log = logging.getLogger("Main.DlProc")
		if not deduper:
			self.log.warning("No deduplication interface!")

		if deduper:
			self.log.info("Scanning archive")

			# load the context of the directory (if needed)
			dirPath = os.path.split(archivePath)[0]

			try:


				dc = deduplicator.archChecker.ArchChecker(archivePath)

				if deleteDups:
					# check hash first, then phash. That way, we get tagging that
					# indicates what triggered the removal.

					bestMatch = dc.getBestBinaryMatch()
					if includePHash and not bestMatch:
						phashMatch = dc.getBestPhashMatch(phashThresh)
					else:
						phashMatch = False

					print("Best  match", bestMatch)
					print("PHash match", phashMatch)

					if bestMatch:
						self.log.warning("Archive not binary unique: '%s'", archivePath)
						self.crossLink(archivePath, bestMatch, isPhash=False)
						dc.deleteArch()
						retTags += " deleted was-duplicate"

					elif phashMatch:
						self.log.warning("Archive not phash unique: '%s'", archivePath)
						self.crossLink(archivePath, phashMatch, isPhash=True)
						dc.deleteArch()
						retTags += " deleted was-duplicate phash-duplicate"
					else:
						self.log.info("Archive Contains unique files. Leaving alone!")

				if not retTags:
					self.log.info("Adding archive to database.")
					dc.addNewArch()

			except:
				self.log.error("Error when doing archive hash-check!")
				self.log.error(traceback.format_exc())
				retTags += " damaged"

		# processNewArchive returns "damaged" or "duplicate" for the corresponding archive states.
		# Since we don't want to upload archives that are either, we skip if retTags is anything other then ""
		# Also, don't upload porn

		if (not self.pron) and (not retTags) and seriesName:
			try:
				self.log.info("Trying to upload file '%s'.", archivePath)
				up.uploadFile(seriesName, archivePath)
				retTags += " uploaded"
			except ConnectionRefusedError:
				self.log.warning("Uploading file failed! Connection Refused!")
			except:
				self.log.error("Uploading file failed! Unknown Error!")
				self.log.error(traceback.format_exc())
		else:
			self.log.info("File not slated for upload: '%s'", archivePath)

		if retTags:
			self.log.info("Applying tags to archive: '%s'", retTags)
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

if __name__ == "__main__":

	import logSetup
	logSetup.initLogging()