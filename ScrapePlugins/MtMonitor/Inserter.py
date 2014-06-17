

import settings
import ScrapePlugins.RetreivalDbBase
import time

class Inserter(ScrapePlugins.RetreivalDbBase.ScraperDbBase):


	loggerPath = "Main.Inserter"
	pluginName = "DB Item Inserter"
	tableName = "mt"
	dbName = settings.dbName



	def insertItems(self, sourceUrl, originName, seriesName, sourceId, flags="picked"):
		self.log.info("Adding item to download = %s, %s, %s, %s, %s", sourceUrl, originName, seriesName, sourceId, flags)
		self.insertIntoDb(retreivalTime=time.time(), sourceUrl=sourceUrl, originName=originName, dlState=0, seriesName=seriesName, sourceId=sourceId, flags=flags)


	def go(self):
		pass