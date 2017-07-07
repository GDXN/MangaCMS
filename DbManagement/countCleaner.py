

import settings
import DbBase
import time

# This is a class used for situations where a script needs access to the database, but I don't
# want to have to write a whole new subclass of the MonitorDbBase.
# Basically, it's a way to abuse the plugin to let me do raw crap with the DB
# It's terrible practice, but laaaazy, and sometimes I do just
# need to hack a one-time-use thing together.

class CountCleaner(DbBase.DbBase):


	loggerPath = "Main.DbCleaner"


	def clean(self):
		self.openDB()
		self.log.info("Flattening item count table.")
		with self.context_cursor() as cur:
			try:
				cur.execute("BEGIN;")
				self._doClean(cur)
				cur.execute("COMMIT;")
			except:
				cur.execute("ROLLBACK;")
				raise

			self.log.info("Item count table consolidated.")
		self.closeDB()


	def _doClean(self, cur):
		cur.execute('''SELECT  sourcesite, dlstate, quantity, id FROM MangaItemCounts;''')
		ret = cur.fetchall()
		items = {}

		for source, state, count, rowid in ret:
			if not source in items:
				items[source] = {}
			if not state in items[source]:
				items[source][state] = count
			else:
				items[source][state] += count

			cur.execute('''DELETE FROM MangaItemCounts WHERE id=%s;''', (rowid, ))

			# print("ret", source, state, count, rowid)
		for source, values in items.items():
			for value, count in values.items():

				cur.execute('''INSERT INTO MangaItemCounts(sourceSite, dlState, quantity) VALUES (%s, %s, %s);''', (source, value, count))

