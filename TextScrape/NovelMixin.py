
import abc

class NovelMixin(metaclass=abc.ABCMeta):
	__metaclass__ = abc.ABCMeta



	def __ensureTableLinkExists(self, cur):
		# Dereference the source table.
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
			tableId = self.__ensureTableLinkExists(cur)

			cur.execute('SELECT dbId FROM book_series WHERE itemName=%s AND itemTable=%s;', (seriesName, tableId))

			ret = cur.fetchone()
			if ret:
				return

			cur.execute('INSERT INTO book_series (itemName, itemTable) VALUES (%s, %s);', (seriesName, tableId))



	def updateNovelAvailable(self, seriesName, availableChapters):

		with self.transaction() as cur:
			tableId = self.__ensureTableLinkExists(cur)

			cur.execute('SELECT dbId FROM book_series WHERE itemName=%s AND itemTable=%s;', (seriesName, tableId))

			ret = cur.fetchone()
			if not ret:
				self.log.error("Item is not in the database! Wat?")
				self.log.error("Item: '%s', sourceTable: '%s'", seriesName, self.tableName)
				raise ValueError

			cur.execute('UPDATE book_series SET availProgress=%s WHERE itemName=%s AND itemTable=%s;', (availableChapters, seriesName, tableId))





