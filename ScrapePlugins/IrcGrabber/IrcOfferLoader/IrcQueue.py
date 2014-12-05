


import webFunctions
import re
import json

import time

import runStatus
import settings
import pickle
import bs4


import ScrapePlugins.IrcGrabber.IrcQueueBase


class TriggerLoader(ScrapePlugins.IrcGrabber.IrcQueueBase.IrcQueueBase):




	loggerPath = "Main.Iro.Fl"
	pluginName = "IrcOffer site Link Retreiver"
	tableKey = "irc-irh"
	dbName = settings.dbName

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	tableName = "MangaItems"

	feedUrls = [
			("http://blah.hawt.co/",                          "blahmanga"),
			("http://stupidcommotion.net/index.php?group=*",  "stupidcommotion"),
			("http://stupidcommotion.net/torako.php?group=*", "stupidcommotion"),
		]

	def getBot(self, packUrl, channel):


		server = "irchighway"

		self.log.info("Fetching page")
		soup = self.wg.getSoup(packUrl)

		self.log.info("Done. Searching")

		header = soup.h1.get_text().strip()
		botname = header.split()[0]
		# print("Header = ", header, "bot = ", botname)

		mainTable = soup.find("table", summary="list")

		ret = []
		for row in mainTable.find_all("tr"):
			item = {}
			rowItems = row.find_all("td")
			if len(rowItems) == 4:
				pkgNum, dummy_dlcnt, size, info = rowItems

				item["pkgNum"] = pkgNum.get_text().strip("#").strip()

				item["server"] = server
				item["channel"] = channel

				sizeText = size.get_text().strip()
				# Skip all files that have sizes in bytes (just header files and shit)
				if "b" in sizeText.lower():
					continue

				if "k" in sizeText.lower():
					item["size"] = float(sizeText.lower().strip("k").strip())/1000.0
				elif "g" in sizeText.lower():
					item["size"] = float(sizeText.lower().strip("g").strip())*1000.0
				else:
					item["size"] = float(sizeText.lower().strip("m").strip())

				item["botName"] = botname
				if info.find("span", class_="selectable"):
					fname = info.find("span", class_="selectable").get_text().strip()
				elif info.find("a"):
					fname = info.a.get_text().strip().split(" ", 2)[-1]
				else:
					raise ValueError
				item["fName"] = fname

				# I'm using the filename+botname for the unique key to the database.
				itemKey = item["fName"]+item["botName"]

				# Skip video files.
				badExts = ['.mkv', '.mp4', '.avi', '.wmv']
				if any([item["fName"].endswith(skipType) for skipType in badExts]):
					# print("Skipping", item)
					continue

				# print(item)
				item = json.dumps(item)
				ret.append((itemKey, item))
			# else:
			# 	print("Bad row? ", row)

			if not runStatus.run:
				self.log.info( "Breaking due to exit flag being set")
				break

		self.log.info("Found %s items", len(ret))
		return ret


	def getMainItems(self):
		# for item in items:
		# 	self.log.info( item)
		#

		self.log.info( "Loading IrcOffer Main Feeds")



		ret = []

		for url, channel in self.feedUrls:
			ret += self.getBot(url, channel)


		self.log.info("All data loaded")
		return ret


if __name__ == "__main__":
	import logSetup
	logSetup.initLogging()
	fl = TriggerLoader()
	# print(fl)
	# fl.getMainItems()

	fl.go()





