
# from . import absImport
# import settings
# import os
# import logging

# # Checks an archive (`archPath`) against the contents of the database
# # accessible via the `settings.dedupApiFile` python file, which
# # uses the absolute-import tool in the current directory.

# # check() returns True if the archive contains any unique items,
# # false if it does not.

# # deleteArch() deletes the archive which has path archPath,
# # and also does the necessary database manipulation to reflect the fact that
# # the archive has been deleted.
# class DedupManager(object):
# 	def __init__(self):
# 		dbModule         = absImport.absImport(settings.dedupApiFile)
# 		if not dbModule:
# 			raise ImportError
# 		self.db = dbModule.DbApi()
# 		self.log = logging.getLogger("Main.Deduper")

# 	def moveFile(self, oldPath, newPath):
# 		self.db.moveItem(oldPath, newPath)

# 	def deletePath(self, path):
# 		self.db.deleteBasePath(path)



# def go():

# 	import logSetup
# 	logSetup.initLogging()

# 	# FIXME

# if __name__ == "__main__":
# 	module = go()

