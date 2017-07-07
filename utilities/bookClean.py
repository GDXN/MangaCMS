# import sys
# sys.path.insert(0,"..")
import os.path

import logSetup
if __name__ == "__main__":
	logSetup.initLogging()


import urllib.parse
import os
import settings
import DbBase
import nameTools as nt


class BookCleaner(DbBase.DbBase):
	loggerPath = "Main.Pc"
	tableName  = "MangaItems"

	def syncNetlocs(self):
		'''
		Some of the old google content has no netloc, and because of how it works, the url isn't a real url (google is annoying).

		Anyways, we check if null, not if an empty string (''), because that delineates between the two.

		'''
		self.openDB()
		self.log.info("Updating any items where the netloc is null")
		with self.context_cursor() as cur:
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
		with self.context_cursor() as cur:
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



	def regenLndbCleanedNames(self):
		self.openDB()
		self.log.info("Regenerating LNDB lookup column table")
		with self.transaction() as cur:
			cur.execute("""SELECT dbid, ctitle FROM books_lndb;""")
			ret = cur.fetchall()
			for dbId, cTitle in ret:
				cleaned = nt.prepFilenameForMatching(cTitle)
				cur.execute("""UPDATE  books_lndb SET cleanedTitle=%s WHERE dbid=%s;""", (cleaned, dbId))
				print(dbId, cleaned, cTitle)

	def cleanMangaUpdatesAuthors(self):
		self.openDB()
		self.log.info("Cleaning up bad author names")
		with self.transaction() as cur:
			cur.execute("""SELECT dbid, buauthor, buartist FROM mangaseries ORDER BY dbid;""")
			ret = cur.fetchall()
			for dbId, auth, illust in ret:
				oldA, oldI = auth, illust
				if auth and " " in auth:
					auth = auth.replace(" ", ' ')
				if illust and " " in illust:
					illust = illust.replace(" ", ' ')

				if auth and auth.replace(" [, Add, ]", "") != auth:
					auth = auth.replace(" [, Add, ]", "").strip()
				elif auth and "[" in auth:
					print("'%s', '%s', '%s'" % (dbId, auth, auth.replace(" [, Add, ]", "")))

				if illust and illust.replace(" [, Add, ]", "") != illust:
					illust = illust.replace(" [, Add, ]", "").strip()
				elif illust and "[" in illust:
					print("'%s', '%s', '%s'" % (dbId, illust, illust.replace(" [, Add, ]", "")))

				if auth != oldA or illust != oldI:
					print("Updating!")
					cur.execute("""UPDATE mangaseries SET buauthor=%s, buartist=%s WHERE dbid=%s;""", (auth, illust, dbId))
				# cleaned = nt.prepFilenameForMatching(cTitle)
				# cur.execute("""UPDATE  books_lndb SET cleanedTitle=%s WHERE dbid=%s;""", (cleaned, dbId))
				# print(dbId, cleaned, cTitle)


	def cleanBookLinkSources(self):
		self.openDB()
		self.log.info("Wat?")
		with self.transaction() as cur:
			cur.execute("""SELECT dbid, src, url FROM book_items;""")
			ret = cur.fetchall()

			items = {}

			for dbid, src, url in ret:
				if not src in items:
					items[src] = set()

				netloc = urllib.parse.urlparse(url).netloc
				if not netloc:
					continue
					# print("WAT?", src, url)


				if 'wordpress.com' in netloc and src != 'wp' and 'wartdf.wordpress.com' not in netloc:
					print(src, url)
					cur.execute('UPDATE book_items SET src=%s WHERE dbid=%s;', ('wp', dbid))


				if 'giraffecorps.liamak.net' in netloc and src != 'wp' and 'wartdf.wordpress.com' not in netloc:
					print(src, url)
					cur.execute('UPDATE book_items SET src=%s WHERE dbid=%s;', ('wp', dbid))

				if 'gravitytranslations.com' in netloc and src != 'wp' and 'wartdf.wordpress.com' not in netloc:
					print(src, url)
					cur.execute('UPDATE book_items SET src=%s WHERE dbid=%s;', ('wp', dbid))


				if '.blogspot.' in netloc and src != 'bs':
					print(src, url)
					cur.execute('UPDATE book_items SET src=%s WHERE dbid=%s;', ('bs', dbid))

				if 'www.taptaptaptaptap.net' in netloc and src != 'bs':
					print(src, url)
					cur.execute('UPDATE book_items SET src=%s WHERE dbid=%s;', ('bs', dbid))

				if 'japtem.com' in netloc and src != 'japtem':
					print(src, url)
					cur.execute('UPDATE book_items SET src=%s WHERE dbid=%s;', ('japtem', dbid))


				if 'www.princerevolution.org' in netloc and src != 'prev':
					print(src, url)
					cur.execute('UPDATE book_items SET src=%s WHERE dbid=%s;', ('prev', dbid))


				if 'guhehe.net' in netloc and src != 'guhehe':
					print(src, url)
					cur.execute('UPDATE book_items SET src=%s WHERE dbid=%s;', ('guhehe', dbid))


				if 'lasolistia.com' in netloc and src != 'hptytl':
					print(src, url)
					cur.execute('UPDATE book_items SET src=%s WHERE dbid=%s;', ('hptytl', dbid))


				# 'www.google.com', 'guhehe.net', 'www.lasolistia.com', 'www.baka-tsuki.org', 'www.guhehe.net', 'lasolistia.com', 'docs.google.com'

				items[src].add((netloc))

			# print(items)

				# print(dbid, src, url)=
			print(items)
		# 	for dbId, cTitle in ret:
		# 		cleaned = nt.prepFilenameForMatching(cTitle)
		# 		cur.execute("""UPDATE  books_lndb SET cleanedTitle=%s WHERE dbid=%s;""", (cleaned, dbId))
		# 		print(dbId, cleaned, cTitle)



def updateNetloc():
	bc = BookCleaner()
	bc.syncNetlocs()

def cleanBookContent():
	bc = BookCleaner()
	bc.purgeStaleFileFromBookContent()



def regenLndbCleanedNames():
	bc = BookCleaner()
	bc.regenLndbCleanedNames()

def fixBookLinkSources():
	bc = BookCleaner()
	bc.cleanBookLinkSources()

def fixMangaUpdatesAuthors():
	bc = BookCleaner()
	bc.cleanMangaUpdatesAuthors()



