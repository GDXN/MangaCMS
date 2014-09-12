
from . import absImport
import settings
import os
import logging

# Checks an archive (`archPath`) against the contents of the database
# accessible via the `settings.dedupApiFile` python file, which
# uses the absolute-import tool in the current directory.

# check() returns True if the archive contains any unique items,
# false if it does not.

# deleteArch() deletes the archive which has path archPath,
# and also does the necessary database manipulation to reflect the fact that
# the archive has been deleted.
class DedupManager(object):
	def __init__(self):
		dbModule         = absImport.absImport(settings.dedupApiFile)
		if not dbModule:
			raise ImportError
		self.db = dbModule.DbApi()
		self.log = logging.getLogger("Main.Deduper")

	def moveFile(self, oldPath, newPath):
		try:
			self.db.moveItem(oldPath, newPath)
		except Exception as e:
			self.db.rollback()
			raise e

	def deletePath(self, path):
		try:
			self.db.deleteBasePath(path)
		except Exception as e:
			self.db.rollback()
			raise e



def go():

	import logSetup
	logSetup.initLogging()

	# FIXME

if __name__ == "__main__":
	module = go()

