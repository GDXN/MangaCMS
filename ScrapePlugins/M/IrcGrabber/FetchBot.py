

import ScrapePlugins.RetreivalDbBase
import ScrapePlugins.M.IrcGrabber.IrcBot
import irc.client

import threading
import nameTools as nt
import settings
import os
import os.path
import time
import json
import runStatus
import traceback

import processDownload

import abc

class DbWrapper(ScrapePlugins.RetreivalDbBase.ScraperDbBase):

	pluginName = "IrcDb Wrapper"

	loggerPath = "Main.Manga.IRC.db"

	dbName = settings.DATABASE_DB_NAME
	tableName = "MangaItems"

	@abc.abstractmethod
	def tableKey(self):
		pass

	# override __init__, catch tabkeKey value, call parent __init__ with the rest of the args
	def __init__(self, *args, **kwargs):
		super(DbWrapper, self).__init__(*args, **kwargs)

	# Have to define go (it's abstract in the parent). We're never going to call it, though.
	def go(self):
		pass


	def retreiveTodoLinkFromDB(self):

		self.resetStuckItems()
		self.log.info( "Fetching items from db...",)

		rows = self.getRowsByValue(dlState=0)

		rows = sorted(rows, key=lambda k: k["retreivalTime"], reverse=True)

		self.log.info( "Done")
		if not rows:
			self.log.info("No new items, nothing to do.")
			return None


		self.log.info( "Have %s new items to retreive in IrcDownloader" % len(rows))

		# Each call returns one item.
		item = rows.pop(0)

		item["retreivalTime"] = time.gmtime(item["retreivalTime"])

		return item


	def getDownloadPath(self, item, fName):

		if not item['seriesName']:
			self.log.info("No series set for item. Guessing from filename:")
			self.log.info("Filename = '%s'", fName)
			bareName = nt.guessSeriesFromFilename(fName)

			# if not matchName or not matchName in nt.dirNameProxy:
			if not nt.haveCanonicalMangaUpdatesName(bareName):
				item["seriesName"] = settings.ircBot["unknown-series"]
			else:
				item["seriesName"] = nt.getCanonicalMangaUpdatesName(bareName)

			self.log.info("Guessed  = '%s'. Updating series information", item['seriesName'])
			self.updateDbEntry(item["sourceUrl"], seriesName=item["seriesName"])


		dlPath, newDir = self.locateOrCreateDirectoryForSeries(item["seriesName"])

		if item["flags"] == None:
			item["flags"] = ""

		if newDir:
			self.updateDbEntry(item["sourceUrl"], flags=" ".join([item["flags"], "haddir"]))
			self.conn.commit()

		fqFName = os.path.join(dlPath, fName)

		loop = 1

		fName, ext = os.path.splitext(fName)

		while os.path.exists(fqFName):
			fName = "%s - (%d).%s" % (fName, loop, ext)
			fqFName = os.path.join(dlPath, fName)
			loop += 1
		self.log.info("Saving to archive = %s", fqFName)


		self.updateDbEntry(item["sourceUrl"], downloadPath=dlPath, fileName=fName, originName=fName)

		return fqFName


class DbXdccWrapper(DbWrapper):
	tableKey = "irc-irh"

class DbTriggerWrapper(DbWrapper):
	tableKey = "irc-trg"



class FetcherBot(ScrapePlugins.M.IrcGrabber.IrcBot.TestBot):


	def __init__(self, xdccInterface, triggerInterface, *args, **kwargs):
		self.xdcc     = xdccInterface
		self.trgr     = triggerInterface

		self.db       = None
		self.run      = True

		self.states   = ["idle", "xdcc requested", "xdcc receiving", "xdcc finished", "xdcc failed"]
		self.state    = "idle"

		self.currentItem = None
		self.todo        = []

		self.timer            = None

		# Time to wait between requesting someing over XDCC, and marking the request as failed due to timeout
		self.xdcc_wait_time   = 120

		super(FetcherBot, self).__init__(*args, **kwargs)

	def get_filehandle(self, fileName):
		# We're already receiving the file at this point, apparently.
		if self.state != "xdcc requested":
			self.log.error("DCC SEND Received when not waiting for DCC transfer! Current state = %s", self.state)
			return False



		fqFName, ext = os.path.splitext(fileName)
		fileName = "%s [IRC]%s" % (fqFName, ext)

		self.currentItem["downloadPath"] = self.db.getDownloadPath(self.currentItem, fileName)
		return open(self.currentItem["downloadPath"], "wb")

	def xdcc_receive_start(self):
		if not self.currentItem:
			self.log.error("DCC Receive start when no item requested?")
			self.changeState("idle")
			return False
		if not self.checkState("xdcc requested"):
			self.log.error("XDCC Transfer started when it was not requested!")
			self.changeState("idle")
			return False
		self.log.info("XDCC Transfer starting!")

		self.changeState("xdcc receiving")
		return True

		# Intercept on on_ctcp, so we can catch errors there (connection failures, etc...)
	def on_ctcp(self, c, e):
		try:
			super().on_ctcp(c, e)
		except (ConnectionRefusedError, irc.client.DCCConnectionError):
			self.log.error("Failed to establish DCC connection!")
			self.log.error(traceback.format_exc())
			self.changeState("xdcc failed")

	def on_dccmsg(self, c, e):
		if not self.checkState("xdcc requested") and \
			not self.checkState("xdcc receiving"):
			self.log.error("DCC Message when not receiving data!")
			try:
				self._dcc_disconnect(c, e)
			except ValueError:
				self.log.error("Connection not yet open, cannot close")

		else:
			super().on_dccmsg(c, e)


	def xdcc_receive_finish(self):
		self.log.info("XDCC Transfer starting!")
		self.changeState("xdcc finished")


		dedupState = processDownload.processDownload(self.currentItem["seriesName"], self.currentItem["downloadPath"], deleteDups=True)
		self.log.info( "Done")

		self.db.addTags(dbId=self.currentItem["dbId"], tags=dedupState)
		if dedupState != "damaged":
			self.db.updateDbEntry(self.currentItem["sourceUrl"], dlState=2)
		else:
			self.db.updateDbEntry(self.currentItem["sourceUrl"], dlState=-10)


	def checkState(self, checkState):
		if not checkState in self.states:
			raise ValueError("Tried to set check if invalid state! Invalid state state = %s" % checkState)
		return self.state == checkState

	def changeState(self, newState):
		if not newState in self.states:
			raise ValueError("Tried to set invalid state! New state = %s" % newState)
		self.log.info("State changing to %s from %s", newState, self.state)
		self.state = newState

	def requestItem(self, reqItem):

		info = json.loads(reqItem["sourceId"])
		reqItem["info"] = info
		# print("info", info["fName"])


		if not "#"+reqItem["info"]["channel"] in self.channels:
			self.log.info("Need to join channel %s", reqItem["info"]["channel"])
			self.log.info("Already on channels %s", self.channels)
			self.connection.join("#"+reqItem["info"]["channel"])
			time.sleep(3)

		self.currentItem = reqItem
		self.changeState("xdcc requested")
		reqStr = "xdcc send %s" % reqItem["info"]["pkgNum"]
		self.connection.privmsg(reqItem["info"]["botName"], reqStr)
		self.log.info("Request = '%s - %s'", reqItem["info"]["botName"], reqStr)

		self.db.updateDbEntry(reqItem["sourceUrl"], seriesName=reqItem["seriesName"], dlState=1)

	def triggerItem(self, reqItem):

		info = json.loads(reqItem["sourceId"])
		print("reqItem = ", reqItem)
		print("Item = ", info)

		if not "#"+info["channel"] in self.channels:
			self.log.info("Need to join channel %s", info["channel"])
			self.log.info("Already on channels %s", self.channels)
			self.connection.join("#"+info["channel"])
			time.sleep(3)

		self.currentItem = reqItem
		self.changeState("xdcc requested")
		self.connection.privmsg("#"+info["channel"], info['trigger'])
		self.log.info("Sending trigger '%s' to '%s'", info['trigger'], info["channel"])

		self.db.updateDbEntry(reqItem["sourceUrl"], dlState=1)

	def markDownloadFailed(self):
		self.log.error("Timed out on XDCC Request!")
		self.log.error("Failed item = '%s'", self.currentItem)
		self.db.updateDbEntry(self.currentItem["sourceUrl"], dlState=-1)
		self.currentItem = None


	def markDownloadFinished(self):
		self.log.info("XDCC Finished!")
		self.log.info("Item = '%s'", self.currentItem)



		self.currentItem = None
		self.received_bytes = 0


	def stepStateMachine(self):
		if self.state == "idle":



			todo = self.xdcc.retreiveTodoLinkFromDB()
			if todo:   # Have something to download via XDCC
				self.db = self.xdcc
				self.requestItem(todo)
				self.timer = time.time()
				return


			todo = self.trgr.retreiveTodoLinkFromDB()
			if todo:   # Have something to download via Trigger
				self.db = self.trgr
				self.triggerItem(todo)
				self.timer = time.time()
				return

			# sleep 30 minutes if there was nothing to do.
			for x in range(30*60):
				time.sleep(1)
				if not runStatus.run:
					break

		elif self.state == "xdcc requested":
			if time.time() - self.timer > self.xdcc_wait_time:
				self.changeState("xdcc failed")

		elif self.state == "xdcc receiving":  # Wait for download to finish
			pass

		elif self.state == "xdcc finished":  # Wait for download to finish
			self.markDownloadFinished()
			self.changeState("idle")

		elif self.state == "xdcc failed":  # Wait for download to finish
			self.markDownloadFailed()
			self.changeState("idle")


	def processQueue(self):
		if not self.run:
			self.die("Whoops, herped my derp.")

		# self.log.info("QueueProcessor")
		if self.state != "idle" and self.received_bytes != 0:
			self.log.info("Current state = %s, rec bytes = %s", self.state, self.received_bytes)
		self.stepStateMachine()

	def welcome_func(self, c, e):
		# Tie periodic calls to on_welcome, so they don't back up while we're connecting.

		self.reactor.execute_every(2.5,     self.processQueue)
		self.log.info("IRC Interface connected to server %s", self.server_list)




class IrcRetreivalInterface(object):
	def __init__(self):
		server = "irc.irchighway.net"

		xdccSource = DbXdccWrapper()
		trgrSource = DbTriggerWrapper()

		self.bot = FetcherBot(xdccSource, trgrSource, settings.ircBot["name"], settings.ircBot["rName"], server)

	def startBot(self):

		self.ircThread = threading.Thread(target=self.bot.startup)
		self.ircThread.start()

	def stopBot(self):
		print("Calling stopBot")
		self.bot.run = False
		print("StopBot Called")





if __name__ == "__main__":
	import logSetup
	import signal


	runner = IrcRetreivalInterface()

	def signal_handler(dummy_signal, dummy_frame):
		if runStatus.run:
			runStatus.run = False
			runner.stopBot()
			print("Telling threads to stop")
		else:
			print("Multiple keyboard interrupts. Raising")
			raise KeyboardInterrupt


	signal.signal(signal.SIGINT, signal_handler)
	logSetup.initLogging()


	runner.startBot()



