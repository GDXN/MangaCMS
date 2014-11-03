

# Ideally, all downloaded archives should run through this function.
import UploadPlugins.Madokami.uploader as up
import archCleaner as ac
import logging
import traceback
import os.path


PHASH_DISTANCE = 2

def processDownload(seriesName, archivePath, pron=False, deleteDups=False, includePHash=False, **kwargs):


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
		retTags = archCleaner.processNewArchive(archivePath, **kwargs)
	except:
		log.critical("Error processing archive '%s'", archivePath)
		log.critical(traceback.format_exc())
		retTags = "corrupt unprocessable"


	log = logging.getLogger("Main.DlProc")
	if not deduper:
		log.warning("No deduplication interface!")

	if deduper:
		log.info("Scanning archive")

		# load the context of the directory (if needed)
		dirPath = os.path.split(archivePath)[0]

		try:


			dc = deduplicator.archChecker.ArchChecker(archivePath)

			if deleteDups:
				# check hash first, then phash. That way, we get tagging that
				# indicates what triggered the removal.
				if not dc.isBinaryUnique():
					log.warning("Archive not binary unique: '%s'", archivePath)
					dc.deleteArch()
					retTags += " deleted was-duplicate"
				elif includePHash and not dc.isPhashUnique(PHASH_DISTANCE):
					log.warning("Archive not phash unique: '%s'", archivePath)
					dc.deleteArch()
					retTags += " deleted was-duplicate phash-duplicate"
				else:
					log.info("Archive Contains unique files. Leaving alone!")

			if not retTags:
				log.info("Adding archive to database.")
				dc.addNewArch()

		except:
			log.error("Error when doing archive hash-check!")
			log.error(traceback.format_exc())
			retTags += " damaged"

	# processNewArchive returns "damaged" or "duplicate" for the corresponding archive states.
	# Since we don't want to upload archives that are either, we skip if retTags is anything other then ""
	# Also, don't upload porn

	if (not retTags and not pron) and seriesName:
		try:
			up.uploadFile(seriesName, archivePath)
			retTags += " uploaded"
		except ConnectionRefusedError:
			log.warning("Uploading file failed! Connection Refused!")
		except:
			log.error("Uploading file failed! Unknown Error!")
			log.error(traceback.format_exc())

	if retTags:
		log.info("Applying tags to archive: '%s'", retTags)
	return retTags.strip()


if __name__ == "__main__":

	import logSetup
	logSetup.initLogging()
	checker = processDownload("TESTING", "/media/Storage/Manga/Junketsu No Maria [+]/Junketsu no Maria v01 c02[fbn].zip", pron=True, deleteDups=True)

	# checker = processDownload("TESTING", "/media/Storage/MP/Chaos;Head - Blue Complex [++];Chaos;Head - Blue Complex v01 c01.zip - Chaos;Head - Blue Complex v01 c01.zip", pron=True, includePHash=True, deleteDups=True)
