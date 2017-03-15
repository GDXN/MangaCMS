


import webFunctions
import re
import json

import time

import runStatus
import settings



import ScrapePlugins.M.IrcGrabber.IrcQueueBase
import ScrapePlugins.M.IrcGrabber.IrcBot



class ListerBot(ScrapePlugins.M.IrcGrabber.IrcBot.TestBot):

	channels = []
	listComplete = False


	def on_liststart(self, dummy_connection, dummy_event):
		self.channels = []

	def on_list(self, dummy_connection, event):
		assert len(event.arguments) == 3
		self.channels.append((event.arguments[0], event.arguments[2]))


	def on_listend(self, dummy_connection, dummy_event):
		self.listComplete = True

	def getList(self):
		self.listComplete = False
		self.connection.list()

		cumTime = 0
		loopTimeout = 0.1
		while not self.listComplete:
			# Kick over the event-loop so it'll parse incoming data while we're waiting for the list to complete
			self.reactor.process_once(timeout=loopTimeout)
			cumTime += loopTimeout

			# Timeout if we've run more then 3 minutes in the list command
			if cumTime > 60*3:
				raise ValueError("List command timed out!")

		ret = self.channels
		self.channels = []
		return ret


	def welcome_func(self, c, e):
		print("Welcomed!")
		# print(self.server_list[0])
		# print(self.connection)

		# print("Listing connection")
		# print(self.getList())


	def connectAndGetList(self):
		self._connect()
		cumTime = 0
		loopTimeout = 0.1
		while not self.welcomed:
			self.reactor.process_once(timeout=loopTimeout)

			# Timeout if we've run more then 5 minutes to connect
			cumTime += loopTimeout
			if cumTime > 60*5:
				raise ValueError("Connection timed out!!")


		self.log.info("Getting list!")

		list = self.getList()

		self.reactor.disconnect_all()

		return list




class ChannelTriggerLoader(ScrapePlugins.M.IrcGrabber.IrcQueueBase.IrcQueueBase):



	loggerPath = "Main.Manga.Chan.Fl"
	pluginName = "Channel trigger Retreiver"
	tableKey = "irc-trg"
	dbName = settings.DATABASE_DB_NAME

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	tableName = "MangaItems"

	feedUrl = "http://vi-scans.com/bort/search.php"

	extractRe = re.compile(r"p\.k\[\d+\] = ({.*?});")


	def getChannels(self):

		bot = ListerBot("Test-bot", "Test-bot-bot", 'irc.irchighway.net')
		print("Bot created. Connecting")
		list = bot.connectAndGetList()
		return list

	def processChannel(self, channelTuple):

		ret = []

		channel, motd = channelTuple


		# Skip channels we don't want (principally used to ignore non-english scanlator groups)
		if channel in settings.ircMotdScraperMaskChannels:
			return []

		triggerRe = re.compile(r'\W(\![a-z]+\d+)\W')

		triggers = triggerRe.findall(motd)
		if triggers:

			for trigger in triggers:

				item = {}
				item["server"] = "irchighway"
				item["channel"] = channel.replace("#", "").strip().lower()

				item["trigger"] = trigger

				itemKey = item["trigger"]+item["channel"]+item["server"]
				item = json.dumps(item)

				# Double-check we're not grabbing a list command
				# This is because I think oneshot-triggers may not
				# Have postpended digits, so I may allow the regex to
				# not require them at some point.
				if trigger != "!list":

					# print(itemKey, item)
					ret.append((itemKey, item))

		return ret


	def getMainItems(self):


		self.log.info( "Loading IRC MOTD Triggers")

		ret = []
		for channel in self.getChannels():
			chanItems = self.processChannel(channel)
			for item in chanItems:
				ret.append(item)

		self.log.info("All data loaded")
		return ret




	def processLinksIntoDB(self, itemDataSets, isPicked=False):

		self.log.info( "Inserting...",)
		newItems = 0

		with self.transaction() as cur:
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
	fl = ChannelTriggerLoader()
	# print(fl)
	# fl.getMainItems()

	# ret = fl.getMainItems()
	# for item in ret:
	# 	print(item)

	fl.go()


