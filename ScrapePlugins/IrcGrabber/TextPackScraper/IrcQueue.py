


import webFunctions
import re

import time
import json
import runStatus
import settings
import nameTools as nt


import ScrapePlugins.IrcGrabber.IrcQueueBase


class TriggerLoader(ScrapePlugins.IrcGrabber.IrcQueueBase.IrcQueueBase):



	loggerPath = "Main.Manga.Txt.Fl"
	pluginName = "Text-Packlist Link Retreiver"
	tableKey = "irc-irh"
	dbName = settings.DATABASE_DB_NAME

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	tableName = "MangaItems"


	# format is ({packlist}, {channel}, {botname})
	baseUrls = [
		("http://fth-scans.com/xdcc.txt",      'halibut', '`FTH`')
		]


	def closeDB(self):
		self.log.info( "Closing DB...",)
		self.conn.close()
		self.log.info( "done")


	def extractRow(self, row, channel, botName):


		skipFtypes = ['.mkv', '.mp4', '.avi', '.wmv']

		item = {}
		item["server"] = "irchighway"
		item["channel"] = channel
		packno, size, filename = row


		item["pkgNum"] = packno.strip("#").strip()
		item["fName"] = filename.strip()
		item["size"] = size.strip()

		nameRe = re.compile("/msg (.+?) xdcc")



		item["botName"] = botName

		# Some of these bots have videos and shit. Skip that
		for skipType in skipFtypes:
			if item["fName"].endswith(skipType):
				return False


		return item

	def getBot(self, chanSet):

		ret = []

		# print("fetching page", botPageUrl)

		botPageUrl, channel, botName = chanSet

		page = self.wg.getpage(botPageUrl)
		rowRe = re.compile('^#(\d+)\W+\d*x\W+\[\W*([\d\.]+)M\]\W+?(.*)$', flags=re.MULTILINE)

		matches = rowRe.findall(page)
		for match in matches:
			item = self.extractRow(match, channel, botName)

			itemKey = item["fName"]+item["botName"]
			item = json.dumps(item)
			ret.append((itemKey, item))

			if not runStatus.run:
				self.log.info( "Breaking due to exit flag being set")
				break

		self.log.info("Found %s items for bot", len(ret))
		return ret

	def getMainItems(self):


		self.log.info( "Loading Text-Pack Feeds")

		ret = []
		for chanSet in self.baseUrls:

			ret += self.getBot(chanSet)

		self.log.info("All data loaded")
		return ret




	def processLinksIntoDB(self, itemDataSets, isPicked=False):

		self.log.info( "Inserting...",)
		newItems = 0

		with self.conn.cursor() as cur:
			cur.execute("BEGIN;")

			for itemKey, itemData in itemDataSets:
				if itemData is None:
					print("itemDataSets", itemDataSets)
					print("WAT")

				row = self.getRowsByValue(limitByKey=False, sourceUrl=itemKey)
				if not row:
					newItems += 1


					# Flags has to be an empty string, because the DB is annoying.
					#
					# TL;DR, comparing with LIKE in a column that has NULLs in it is somewhat broken.
					#
					self.insertIntoDb(retreivalTime = time.time(),
										sourceUrl   = itemKey,
										sourceId    = itemData,
										dlState     = 0,
										flags       = '',
										commit=False)

					self.log.info("New item: %s", itemData)


			self.log.info( "Done")
			self.log.info( "Committing...",)
			cur.execute("COMMIT;")
			self.log.info( "Committed")

		return newItems


	def go(self):

		self.resetStuckItems()
		self.log.info("Getting feed items")

		feedItems = self.getMainItems()
		self.log.info("Processing feed Items")

		self.processLinksIntoDB(feedItems)
		self.log.info("Complete")


if __name__ == "__main__":
	import logSetup
	logSetup.initLogging()
	fl = TriggerLoader()
	# print(fl)
	# fl.getMainItems()

	fl.go()


