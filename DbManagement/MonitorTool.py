

import settings
import ScrapePlugins.MonitorDbBase
import time

class Inserter(ScrapePlugins.MonitorDbBase.MonitorDbBase):


	loggerPath = "Main.Inserter"
	pluginName = "DB Item Inserter"
	tableName = "MangaSeries"
	dbName = settings.dbName


	def go(self):
		pass