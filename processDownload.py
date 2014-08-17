

# Ideally, all downloaded archives should run through this function.
# Currently, it's just a few plugins where I've patched it in.
import UploadPlugins.Madokami.uploader as up
import archCleaner as ac
import logging
import traceback

def processDownload(seriesName, archivePath, pron=False, **kwargs):
	archCleaner = ac.ArchCleaner()
	log = logging.getLogger("Main.DlProc")
	dedupState = archCleaner.processNewArchive(archivePath, **kwargs)

	# processNewArchive returns "damaged" or "duplicate" for the corresponding archive states.
	# Since we don't want to upload either, we skip if dedupState is anything other then ""
	# Also, don't upload porn
	if not dedupState and not pron:
		try:
			up.uploadFile(seriesName, archivePath)
		except ConnectionRefusedError:
			log.warning("Uploading file failed! Connection Refused!")
		except:
			log.error("Uploading file failed! Unknown Error!")
			log.error(traceback.format_exc())


	return dedupState

