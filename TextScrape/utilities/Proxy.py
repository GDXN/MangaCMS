
import logSetup
if __name__ == "__main__":
	print("Initializing logging")
	logSetup.initLogging()

import TextScrape.SiteArchiver
import os

class EmptyProxy(TextScrape.SiteArchiver.SiteArchiver):

	tableKey   = 'none'
	loggerPath = 'Main.Text.Util'
	pluginName = 'DbFixer'
	badwords   = []
	baseUrl    = []
	startUrl   = []


	def __init__(self, tableKey, tableName, scanned):
		self.tableKey       = tableKey
		self.tableName      = tableName
		self.baseUrl        = scanned


		super().__init__()
