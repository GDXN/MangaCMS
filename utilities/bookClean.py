# import sys
# sys.path.insert(0,"..")
import os.path

import logSetup
if __name__ == "__main__":
	logSetup.initLogging()


import urllib.parse
import os
import settings
import ScrapePlugins.DbBase
import ScrapePlugins.RetreivalDbBase


class BookCleaner(ScrapePlugins.DbBase.DbBase):
	loggerPath = "Main.Pc"
	tableName  = "MangaItems"

	def syncNetlocs(self):
		'''
		Some of the old google content has no netloc, and because of how it works, the url isn't a real url (google is annoying).

		Anyways, we check if null, not if an empty string (''), because that delineates between the two.

		'''
		self.openDB()
		self.log.info("Updating any items where the netloc is null")
		cur = self.conn.cursor()
		cur.execute("BEGIN;")

		cur.execute('''SELECT dbid, url, netloc FROM book_items WHERE netloc IS NULL;''')
		ret = cur.fetchall()
		for dbid, url, old_netloc in ret:
			if old_netloc != None:
				raise ValueError("netloc is not null?")

			urlParam = urllib.parse.urlparse(url)
			cur.execute('''UPDATE book_items SET netloc=%s WHERE dbid=%s;''', (urlParam.netloc, dbid))


		self.log.info("Fixing google document content.")

		cur.execute('''SELECT dbid, url, netloc FROM book_items WHERE netloc = '';''')
		ret = cur.fetchall()
		for dbid, url, old_netloc in ret:
			if old_netloc != '':
				raise ValueError("netloc is not null?")
			urlParam = urllib.parse.urlparse(url)

			cur.execute('''UPDATE book_items SET netloc=%s WHERE dbid=%s;''', ('docs.google.com', dbid))



		self.log.info("All null netlocs updated. Committing changes.")
		cur.execute("COMMIT;")
		self.log.info("Committed. Complete.")


	def loadCacheFiles(self):
		self.log.info("Loading files from cache directory into memory")
		cachePath = settings.bookCachePath

		ret = set()
		loaded = 0

		for root, dirs, files in os.walk(cachePath):
			for name in files:
				fileP = os.path.join(root, name)
				if not os.path.exists(fileP):
					raise ValueError
				ret.add(fileP)

				loaded += 1
				if loaded % 5000 == 0:
					self.log.info("Loaded files: %s", loaded)

		self.log.info("%s Filesystem Files Loaded", len(ret))
		return ret

	def loadDatabaseFiles(self):
		self.log.info("Loading files from database into memory")
		cur = self.conn.cursor()
		cur.execute("BEGIN;")

		cur.execute('''SELECT dbid, fspath FROM book_items WHERE fspath IS NOT NULL AND fspath <> '';''')
		data = cur.fetchall()
		self.log.info('Fetched items from database: %s', len(data))
		cur.execute("COMMIT;")
		self.log.info("DB Files Loaded")

		ret = {}
		for dbid, fspath in data:
			ret.setdefault(fspath, set()).add(dbid)
		self.log.info('Distinct items on filesystem: %s', len(ret))

		return ret


	def purgeStaleFileFromBookContent(self):
		self.openDB()
		self.log.info("Fetching resources from database and filesystem.")
		fsFiles = self.loadCacheFiles()
		dbFiles = self.loadDatabaseFiles()
		self.log.info("Trimming all content from the book content cache that has gone stale.")

		for itemPath in dbFiles.keys():
			if itemPath in fsFiles:
				fsFiles.remove(itemPath)
			else:
				self.log.warn("Cannot find item: '%s'", itemPath)

		self.log.info("Remaining unlinked files: %s. Deleting", len(fsFiles))
		for file in fsFiles:
			os.unlink(file)
		self.log.info("Trim Complete.")

def updateNetloc():
	bc = BookCleaner()
	bc.syncNetlocs()

def cleanBookContent():
	bc = BookCleaner()
	bc.purgeStaleFileFromBookContent()


