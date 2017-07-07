


import webFunctions
import re

import time
import json
import runStatus
import settings
import nameTools as nt


import ScrapePlugins.M.IrcGrabber.IrcQueueBase


class TriggerLoader(ScrapePlugins.M.IrcGrabber.IrcQueueBase.IrcQueueBase):



	loggerPath = "Main.Manga.Im.Fl"
	pluginName = "Illuminati-Manga Link Retreiver"
	tableKey = "irc-irh"
	dbName = settings.DATABASE_DB_NAME

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	tableName = "MangaItems"

	baseUrl = "http://www.illuminati-manga.com/?page_id=17782"

	def getBotUrls(self):
		botPage = self.wg.getSoup(self.baseUrl)
		bots = botPage.find('div', class_='xdcc-list-bots')

		botUrls = []
		for bot in bots.find_all("a"):
			if not 'raw' in bot.string.lower():
				botUrls.append(bot['data-url'])
		return botUrls


	def extractRow(self, row):

		skipFtypes = ['.mkv', '.mp4', '.avi', '.wmv']

		item = {}
		item["server"] = "irchighway"
		item["channel"] = "illuminati-manga"
		packno, fetches, size, filename = row.find_all("td")


		item["pkgNum"] = packno.get_text().strip("#").strip()
		item["fName"] = filename.get_text().strip()
		item["size"] = size.get_text().strip()

		nameRe = re.compile("/msg (.+?) xdcc")

		nameMatch = nameRe.search(filename['title'])

		item["botName"] = nameMatch.group(1)

		# Some of these bots have videos and shit. Skip that
		for skipType in skipFtypes:
			if item["fName"].endswith(skipType):
				return False


		return item

	def getBot(self, botPageUrl):

		ret = []

		# print("fetching page", botPageUrl)

		soup = self.wg.getSoup(botPageUrl)
		itemTable = soup.find("table", attrs={'summary': 'list'})

		for row in itemTable.tbody.find_all("tr"):
			item = self.extractRow(row)

			if not item:
				continue


			itemKey = item["fName"]+item["botName"]
			item = json.dumps(item)
			ret.append((itemKey, item))

			if not runStatus.run:
				self.log.info( "Breaking due to exit flag being set")
				break

		self.log.info("Found %s items for bot", len(ret))
		return ret

	def getMainItems(self):


		self.log.info( "Loading ViScans Main Feed")

		bots = self.getBotUrls()

		ret = []
		for bot in bots:
			botItems = self.getBot(bot)
			for item in botItems:
				ret.append(item)


		self.log.info("All data loaded")
		return ret





if __name__ == "__main__":
	import logSetup
	logSetup.initLogging()
	fl = TriggerLoader()
	# print(fl)
	# fl.getMainItems()
	fl.go()
	# print(fl.getBot('http://94.23.195.195:8000/?'))


