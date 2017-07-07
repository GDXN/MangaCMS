

import settings
import DbBase
import time


class LogTrimmer(DbBase.DbBase):


	loggerPath = "Main.LogCleaner"


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
		thresholdTime = time.time() - settings.maxLogAge
		cur.execute('''DELETE FROM logTable WHERE time<%s;''', (thresholdTime, ))


