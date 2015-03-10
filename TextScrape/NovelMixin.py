
import abc

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






