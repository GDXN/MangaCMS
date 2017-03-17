


import webFunctions
import re

import time
import json
import runStatus
import settings
import nameTools as nt


import ScrapePlugins.M.IrcGrabber.IrcQueueBase


class TriggerLoader(ScrapePlugins.M.IrcGrabber.IrcQueueBase.IrcQueueBase):



	loggerPath = "Main.Manga.Cat.Fl"
	pluginName = "Cat-Chans Trigger Retreiver"
	tableKey = "irc-trg"
	dbName = settings.DATABASE_DB_NAME

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	tableName = "MangaItems"

	baseUrl = "http://thecatscans.wordpress.com/"

	def getBot(self, botPageUrl):

		ret = []

		# print("fetching page", botPageUrl)

		page = self.wg.getSoup(botPageUrl)

		triggerRe = re.compile(r'\W(\![a-z]+\d+)\W')

		contentDivs = page.find_all("div", class_='entry-content')
		for div in contentDivs:
			post = div.get_text()
			triggers = triggerRe.findall(post)

			for trigger in triggers:

				item = {}
				item["server"] = "irchighway"
				item["channel"] = "CATscans"

				item["trigger"] = trigger

				itemKey = item["trigger"]+item["channel"]+item["server"]
				item = json.dumps(item)

				ret.append((itemKey, item))

		return ret


	def getMainItems(self):


		self.log.info( "Loading Cat Scans Main Feed")

		ret = self.getBot(self.baseUrl)

		self.log.info("All data loaded")
		return ret





if __name__ == "__main__":
	import logSetup
	logSetup.initLogging()
	fl = TriggerLoader()
	# print(fl)
	# fl.getMainItems()

	# ret = fl.getMainItems()
	# print(ret)

	fl.go()


