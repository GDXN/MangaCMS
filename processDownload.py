

# Ideally, all downloaded archives should run through this function.
# Currently, it's just a few plugins where I've patched it in.
import UploadPlugins.Madokami.uploader as up
import archCleaner as ac

def processDownload(seriesName, archivePath, pron=False, **kwargs):
	archCleaner = ac.ArchCleaner()

	dedupState = archCleaner.processNewArchive(archivePath, **kwargs)

	# processNewArchive returns "damaged" or "duplicate" for the corresponding archive states.
	# Since we don't want to upload either, we skip if dedupState is anything other then ""
	# Also, don't upload porn
	if not dedupState and not pron:
		up.uploadFile(seriesName, archivePath)

	return dedupState

