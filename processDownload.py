

# Ideally, all downloaded archives should run through this function.
# Currently, it's just a few plugins where I've patched it in.
import UploadPlugins.Madokami.uploader as up
import archCleaner as ac
import logging
import traceback

def processDownload(seriesName, archivePath, pron=False, **kwargs):
	archCleaner = ac.ArchCleaner()
	log = logging.getLogger("Main.DlProc")
	try:
		retTags = archCleaner.processNewArchive(archivePath, **kwargs)
	except:
		log.critical("Error processing archive '%s'", archivePath)
		log.critical(traceback.format_exc())
		retTags = "corrupt unprocessable"

	# processNewArchive returns "damaged" or "duplicate" for the corresponding archive states.
	# Since we don't want to upload either, we skip if retTags is anything other then ""
	# Also, don't upload porn
	if not retTags and not pron:
		try:
			up.uploadFile(seriesName, archivePath)
			retTags += " uploaded"
		except ConnectionRefusedError:
			log.warning("Uploading file failed! Connection Refused!")
		except:
			log.error("Uploading file failed! Unknown Error!")
			log.error(traceback.format_exc())


	return retTags.strip()

