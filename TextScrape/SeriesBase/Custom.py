
import logSetup
if __name__ == "__main__":
	print("Initializing logging")
	logSetup.initLogging()

import TextScrape.MonitorBase
import TextScrape.NovelMixin

class CustomMonitor(TextScrape.NovelMixin.NovelMixin, TextScrape.MonitorBase.MonitorBase):
	tableName = 'books_custom'
	loggerPath = 'Main.Text.Custom.Monitor'
	pluginName = 'CustomMonitor'
	plugin_type = 'SeriesMonitor'

	def setupNovelTable(self):
		cur = self.conn.cursor()
		# Commit has to be explicit, because _getEnsureTableLinkExists() assumes it's
		# being called within a transaction
		cur.execute("BEGIN;")
		self._getEnsureTableLinkExists(cur)
		cur.execute("COMMIT;")

	def go(self):
		self.setupNovelTable()
		pass

def test():
	scrp = CustomMonitor()
	scrp.go()
	# scrp.retreiveItemFromUrl(scrp.startUrl)


if __name__ == "__main__":
	test()




