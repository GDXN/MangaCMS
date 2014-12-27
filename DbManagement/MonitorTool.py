

import settings
import ScrapePlugins.MonitorDbBase
import ScrapePlugins.RetreivalBase
import time

# This is a class used for situations where a script needs access to the database, but I don't
# want to have to write a whole new subclass of the MonitorDbBase.
# Basically, it's a way to abuse the plugin to let me do raw crap with the DB
# It's terrible practice, but laaaazy, and sometimes I do just
# need to hack a one-time-use thing together.

class Inserter(ScrapePlugins.MonitorDbBase.MonitorDbBase):


	loggerPath = "Main.Inserter"
	pluginName = "DB Item Inserter"
	tableName = "MangaSeries"
	dbName = settings.DATABASE_DB_NAME


	def go(self):
		pass


class Scraper(ScrapePlugins.RetreivalBase.ScraperBase):


	loggerPath = "Main.Inserter"
	pluginName = "DB Item Inserter"
	tableName = "MangaSeries"
	dbName = settings.DATABASE_DB_NAME


	def go(self):
		pass