

# Ideally, all downloaded archives should run through this function.
import UploadPlugins.Madokami.uploader as up
import archCleaner as ac
import logging
import traceback



try:
	import deduplicator.dupCheck as deduper
	print("Have file deduplication interface. Doing download duplicate checking!")
except:
	deduper = None
	print("No deduplication tools installed.")

def processDownload(seriesName, archivePath, pron=False, deleteDups=False, includePHash=False, **kwargs):


	log = logging.getLogger("Main.ArchProc")

	archCleaner = ac.ArchCleaner()
	log = logging.getLogger("Main.DlProc")
	try:
		retTags = archCleaner.processNewArchive(archivePath, **kwargs)
	except:
		log.critical("Error processing archive '%s'", archivePath)
		log.critical(traceback.format_exc())
		retTags = "corrupt unprocessable"

	if not deduper:
		log.warning("No deduplication interface!")

	if deduper and deleteDups:
		log.info("Scanning archive for duplicates")
		dc = deduper.ArchChecker(archivePath)

		# check hash first, then phash. That way, we get tagging that
		# indicates what triggered the removal.
		if not dc.isBinaryUnique():
			log.warning("Archive not binary unique: '%s'", archivePath)
			dc.deleteArch()
			retTags += " deleted was-duplicate"
		elif includePHash and not dc.isPhashUnique():
			log.warning("Archive not phash unique: '%s'", archivePath)
			dc.deleteArch()
			retTags += " deleted was-duplicate phash-duplicate"
		else:
			log.info("Archive Contains unique files. Leaving alone!")
			dc.addNewArch()


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

