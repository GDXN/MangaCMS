

import settings
import ScrapePlugins.RetreivalDbBase


class ScraperDbTool(ScrapePlugins.RetreivalDbBase.ScraperDbBase):


	loggerPath       = "Main.Util.Base"
	pluginName       = "None"
	tableName        = "HentaiItems"


	dbName = settings.dbName

	tableKey = "NA"


	def go(self):
		pass

