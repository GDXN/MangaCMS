


import webFunctions
import re
import json

import time

import runStatus
import settings
import pickle
import bs4


import ScrapePlugins.IrcGrabber.IrcQueueBase


class StupidCommotionTriggerLoader(ScrapePlugins.IrcGrabber.IrcQueueBase.IrcQueueBase):



	wg = webFunctions.WebGetRobust()
	loggerPath = "Main.SC.Fl"
	pluginName = "StupidCommotion Link Retreiver"
	tableKey = "sc"
	dbName = settings.dbName

	tableName = "MangaItems"

	feedUrls = ["http://stupidcommotion.net/index.php?group=*",
				"http://stupidcommotion.net/torako.php?group=*"]

	extractRe = re.compile(r"p\.k\[\d+\] = ({.*?});")


	def getMainItems(self, rangeOverride=None, rangeOffset=None):
		# for item in items:
		# 	self.log.info( item)
		#

		self.log.info( "Loading Suzume/Torako Main Feeds")

		channel = "stupidcommotion"
		server = "irchighway"
		ret = []

		for url in self.feedUrls:
			page = self.wg.getpage(url)

			self.log.info("Processing itemList markup....")
			soup = bs4.BeautifulSoup(page)
			self.log.info("Done. Searching")

			header = soup.h1.get_text().strip()
			botname = header.split()[0]
			print("Header = ", header, "bot = ", botname)

			mainTable = soup.find("table", summary="list")

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
					if "b" in sizeText:
						continue

					if "k" in sizeText:
						item["size"] = int(sizeText.strip("k").strip())/1000.0
					else:
						item["size"] = int(sizeText.strip("M").strip())

					item["botName"] = botname
					item["fName"] = info.find("span", class_="selectable").get_text().strip()

					# I'm using the filename+botname for the unique key to the database.
					itemKey = item["fName"]+item["botName"]
					# print(item)
					item = json.dumps(item)

					ret.append((itemKey, item))
				else:
					print("Bad row? ", row)

				if not runStatus.run:
					self.log.info( "Breaking due to exit flag being set")
					break


		self.log.info("All data loaded")
		return ret


