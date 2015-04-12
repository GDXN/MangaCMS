
import abc
import settings
import hashlib
import os
import os.path
import nameTools

class NovelMixin(metaclass=abc.ABCMeta):
	__metaclass__ = abc.ABCMeta



	def _getEnsureTableLinkExists(self, cur):
		# Dereference the source table.
		while 1:
			cur.execute('SELECT dbId FROM book_series_table_links WHERE tableName=%s;', (self.tableName, ))
			ret = cur.fetchone()
			if ret:
				return ret[0]

			self.log.info("First run for table %s? Inserting table name into linkTable.", self.tableName)
			cur.execute('INSERT INTO book_series_table_links (tableName) VALUES (%s) RETURNING dbId;', (self.tableName, ))
			ret = cur.fetchone()

			assert bool(ret)
			return ret[0]


	def _getEnsureCoverDbExists(self, cur):
		# Dereference the source table.

		cur.execute('''
				CREATE TABLE IF NOT EXISTS
					series_covers
				(
					id                 SERIAL PRIMARY KEY,
					srcTable           TEXT NOT NULL,
					srcId              INTEGER,

					filename           TEXT,
					vol                FLOAT,
					chapter            FLOAT,
					description        TEXT,

					relPath            TEXT NOT NULL,
					fileHash           TEXT NOT NULL,

					constraint series_covers_unique unique (srcTable, fileHash)

				);''')


	def saveFileFromHash(self, fHash, filename, fileCont):
		if not os.path.exists(settings.coverDirectory):
			self.log.warn("Cache directory for book items did not exist. Creating")
			self.log.warn("Directory at path '%s'", settings.coverDirectory)
			os.makedirs(settings.coverDirectory)


		ext = os.path.splitext(filename)[-1]

		ext   = ext.lower()
		fHash = fHash.upper()

		# use the first 3 chars of the hash for the folder name.
		# Since it's hex-encoded, that gives us a max of 2^12 bits of
		# directories, or 4096 dirs.
		dirName = fHash[:3]

		dirPath = os.path.join(settings.coverDirectory, dirName)
		if not os.path.exists(dirPath):
			os.makedirs(dirPath)

		ext = os.path.splitext(filename)[-1]

		ext   = ext.lower()
		fHash = fHash.upper()

		# The "." is part of the ext.
		filename = '{filename}{ext}'.format(filename=fHash, ext=ext)

		fqpath = os.path.join(dirPath, filename)
		fqpath = os.path.abspath(fqpath)
		if not fqpath.startswith(settings.coverDirectory):
			raise ValueError("Generating the file path to save a cover produced a path that did not include the storage directory?")

		locpath = fqpath[len(settings.coverDirectory):]

		with open(fqpath, "wb") as fp:
			fp.write(fileCont)

		return locpath

	def checkFileFromHash(self, cur, inHash):
		cur.execute("""
				SELECT
					srcTable,
					srcId,
					filename
				FROM
					series_covers
				WHERE
					filehash=%s
				;
			""", (inHash, ))
		return cur.fetchall()

	def checkHaveCover(self, seriesId, vol=None, chp=None):
		with self.transaction() as cur:

			# Do some (UGLY) dynamic query stuff.
			# Basically, you can check if 'x = {value}', but
			# 'x = NULL' always returns false, so you have to
			# replace it with 'x is NULL'
			cur.execute("""
				SELECT
					COUNT(*)
				FROM
					series_covers
				WHERE
						srcTable = %s
					AND
						srcId    = %s
					AND
						vol      {vol} %s
					AND
						chapter  {chp} %s
				;
				""".format(
						vol= "is" if not vol else "=",
						chp= "is" if not chp else "=",
					),
				(self.tableName, seriesId, vol, chp))

			quantity = cur.fetchone()[0]

		return quantity



	def upsertCover(self, filename, filecont, seriesId, vol=None, chp=None, description=None, sourceId=None):

		m = hashlib.md5()
		m.update(filecont)
		filehash = m.hexdigest()

		with self.transaction() as cur:
			tableId = self._getEnsureCoverDbExists(cur)


			extant = self.checkFileFromHash(cur, filehash)
			if extant:
				self.log.warning("Already have cover! %s (buid: %s)", extant, sourceId)
				return

			fPath = self.saveFileFromHash(filehash, filename, filecont)

			cur.execute('''
					INSERT INTO
						series_covers
						(

							srcTable,
							srcId,

							filename,
							filehash,

							vol,
							chapter,

							description,
							relPath
						)
					VALUES
						(%s, %s, %s, %s, %s, %s, %s, %s)
					RETURNING id;''', (self.tableName, seriesId, filename, filehash, vol, chp, description, fPath))

			dbId = cur.fetchone()[0]

		return dbId

	def upsertNovelName(self, seriesName):

		with self.transaction() as cur:
			tableId = self._getEnsureTableLinkExists(cur)

			cur.execute('SELECT dbId FROM book_series WHERE itemName=%s AND itemTable=%s;', (seriesName, tableId))

			ret = cur.fetchone()
			if ret:
				return

			self.log.info("Novel Upsert: '%s'!", seriesName)
			cur.execute('INSERT INTO book_series (itemName, itemTable) VALUES (%s, %s);', (seriesName, tableId))



	def updateNovelAvailable(self, seriesName, availableChapters):

		with self.transaction() as cur:
			tableId = self._getEnsureTableLinkExists(cur)

			cur.execute('SELECT dbId, availProgress FROM book_series WHERE itemName=%s AND itemTable=%s;', (seriesName, tableId))

			ret = cur.fetchone()

			if not ret and '(Novel)' in seriesName:
				self.log.warn("Item is not in the database! Wat?")
				self.log.warn("Item: '%s', sourceTable: '%s'", seriesName, self.tableName)
				return
			elif not ret:
				return

			dummy_dbId, progress = ret

			# Only do the update if the new number is actually larger, or if it's been set to -2 (e.g. "Complete")
			if progress >= availableChapters or (availableChapters == -2 and availableChapters != progress):
				return
			cur.execute('UPDATE book_series SET availProgress=%s WHERE itemName=%s AND itemTable=%s;', (availableChapters, seriesName, tableId))


	def updateNovelRead(self, seriesName, readChapters):

		with self.transaction() as cur:
			tableId = self._getEnsureTableLinkExists(cur)

			cur.execute('SELECT dbId, readingprogress FROM book_series WHERE itemName=%s AND itemTable=%s;', (seriesName, tableId))

			ret = cur.fetchone()
			if not ret and '(Novel)' in seriesName:
				self.log.warn("Item is not in the database! Wat?")
				self.log.warn("Item: '%s', sourceTable: '%s'", seriesName, self.tableName)
				return
			elif not ret:
				return

			dummy_dbId, progress = ret
			# Only do the update if the new number is actually larger, or if it's been set to -2 (e.g. "Complete")
			if progress >= readChapters or (readChapters == -2 and readChapters != progress):
				return
			cur.execute('UPDATE book_series SET readingprogress=%s WHERE itemName=%s AND itemTable=%s;', (readChapters, seriesName, tableId))


	def updateNovelTags(self, seriesName, tags):
		if isinstance(tags, str):
			tags = set(tags.lower().split(" "))

		with self.transaction() as cur:

			tableId = self._getEnsureTableLinkExists(cur)
			cur.execute('SELECT dbId FROM book_series WHERE itemName=%s AND itemTable=%s;', (seriesName, tableId))
			ret = cur.fetchone()
			assert bool(ret)
			itemId = ret[0]

			for tag in tags:
				cur.execute('SELECT tagname FROM book_series_tags WHERE seriesid=%s AND tagname=%s;', (itemId, tag))
				ret = cur.fetchone()
				if not ret:
					cur.execute('INSERT INTO book_series_tags (seriesid, tagname) VALUES (%s, %s)', (itemId, tag))






