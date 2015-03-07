
import abc

class NovelMixin(metaclass=abc.ABCMeta):
	__metaclass__ = abc.ABCMeta



	def __getEnsureTableLinkExists(self, cur):
		# Dereference the source table.
		while 1:
			cur.execute('SELECT dbId FROM book_series_table_links WHERE tableName=%s;', (self.tableName, ))
			ret = cur.fetchone()
			if ret:
				return ret[0]

			self.log.info("First run for table %s? Inserting table name into linkTable.")
			cur.execute('INSERT INTO book_series_table_links (tableName) VALUES (%s) RETURNING dbId;', (self.tableName, ))
			ret = cur.fetchone()

			assert bool(ret)
			return ret[0]



	def upsertNovelName(self, seriesName):
		with self.transaction() as cur:
			tableId = self.__getEnsureTableLinkExists(cur)

			cur.execute('SELECT dbId FROM book_series WHERE itemName=%s AND itemTable=%s;', (seriesName, tableId))

			ret = cur.fetchone()
			if ret:
				return

			self.log.info("Novel Upsert: '%s'!", seriesName)
			cur.execute('INSERT INTO book_series (itemName, itemTable) VALUES (%s, %s);', (seriesName, tableId))



	def updateNovelAvailable(self, seriesName, availableChapters):

		with self.transaction() as cur:
			tableId = self.__getEnsureTableLinkExists(cur)

			cur.execute('SELECT dbId FROM book_series WHERE itemName=%s AND itemTable=%s;', (seriesName, tableId))

			ret = cur.fetchone()
			if not ret:
				self.log.error("Item is not in the database! Wat?")
				self.log.error("Item: '%s', sourceTable: '%s'", seriesName, self.tableName)
				raise ValueError

			cur.execute('UPDATE book_series SET availProgress=%s WHERE itemName=%s AND itemTable=%s;', (availableChapters, seriesName, tableId))


	def updateNovelTags(self, seriesName, tags):
		if isinstance(tags, str):
			tags = set(tags.lower().split(" "))

		with self.transaction() as cur:

			tableId = self.__getEnsureTableLinkExists(cur)
			cur.execute('SELECT dbId FROM book_series WHERE itemName=%s AND itemTable=%s;', (seriesName, tableId))
			ret = cur.fetchone()
			assert bool(ret)
			itemId = ret[0]

			for tag in tags:
				cur.execute('SELECT tagname FROM book_series_tags WHERE seriesid=%s AND tagname=%s;', (itemId, tag))
				ret = cur.fetchone()
				if not ret:
					cur.execute('INSERT INTO book_series_tags (seriesid, tagname) VALUES (%s, %s)', (itemId, tag))






