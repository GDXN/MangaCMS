


import webFunctions
import re
import yaml
import json

import time

import runStatus
import settings
import logging


import ScrapePlugins.IrcGrabber.IrcQueueBase






# class IrcRetreivalInterface(object):
# 	def __init__(self):
# 		server = "irc.irchighway.net"

# 		xdccSource = DbXdccWrapper()
# 		trgrSource = DbTriggerWrapper()

# 		self.bot = FetcherBot(xdccSource, trgrSource, settings.ircBot["name"], settings.ircBot["rName"], server)

import ssl
import irc.logging
import irc.buffer
import irc.client
import irc.bot
import irc.strings
import ScrapePlugins.IrcGrabber.IrcBot

class TestBot(irc.bot.SingleServerIRCBot):


	channels = []
	listComplete = False

	def __init__(self, nickname, realname, server, port=9999):
		ssl_factory = irc.connection.Factory(wrapper=ssl.wrap_socket)

		# Horrible monkey-patch the ServerConnection instance so we can fix some encoding issues.
		print("Old buffer class", irc.client.ServerConnection.buffer_class)
		irc.client.ServerConnection.buffer_class = ScrapePlugins.IrcGrabber.IrcBot.TolerantDecodingLineBuffer
		print("New buffer class", irc.client.ServerConnection.buffer_class)

		irc.bot.SingleServerIRCBot.__init__(self, [(server, port)], nickname, realname, connect_factory=ssl_factory)

		self.log = logging.getLogger("Main.List.IRC")
		self.received_bytes = 0

		self.welcomed = False


	# List events:

	def on_liststart(self, dummy_connection, event):
		self.channels = []

	def on_list(self, dummy_connection, event):
		assert len(event.arguments) == 3
		self.channels.append((event.arguments[0], event.arguments[2]))


	def on_listend(self, dummy_connection, dummy_event):
		self.listComplete = True



	# Exposed list functions

	def getList(self):
		self.listComplete = False
		self.connection.list()

		cumTime = 0
		loopTimeout = 0.1
		while not self.listComplete:
			# Kick over the event-loop so it'll parse incoming data while we're waiting for the list to complete
			self.ircobj.process_once(timeout=loopTimeout)
			cumTime += loopTimeout

			# Timeout if we've run more then 3 minutes in the list command
			if cumTime > 60*3:
				raise ValueError("List command timed out!")

		ret = self.channels
		self.channels = []
		return ret


	def startup(self):
		self.log.info("Bot entering select loop")
		self.start()







class ChannelTriggerLoader(ScrapePlugins.IrcGrabber.IrcQueueBase.IrcQueueBase):



	loggerPath = "Main.Chan.Fl"
	pluginName = "Channel trigger Retreiver"
	tableKey = "irc-trg"
	dbName = settings.dbName

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	tableName = "MangaItems"

	feedUrl = "http://vi-scans.com/bort/search.php"

	extractRe = re.compile(r"p\.k\[\d+\] = ({.*?});")


	def closeDB(self):
		self.log.info( "Closing DB...",)
		self.conn.close()
		self.log.info( "done")



	def getBot(self, botPageUrl):

		ret = []

		# print("fetching page", botPageUrl)

		# Hurrah for XML feeds!
		page = self.wg.getSoup(botPageUrl)

		triggerRe = re.compile(r'\W(\![a-z]+\d+)\W')

		entries = page.find_all("entry")
		for entry in entries:
			post = entry.content.get_text()
			triggers = triggerRe.findall(post)

			for trigger in triggers:

				item = {}
				item["server"] = "irchighway"
				item["channel"] = "renzokusei"

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

	ret = fl.getMainItems()
	# for item in ret:
	# 	print(item)

	fl.go()


