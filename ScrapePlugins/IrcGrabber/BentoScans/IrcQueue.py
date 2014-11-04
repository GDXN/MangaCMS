


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




	loggerPath = "Main.Ben.Fl"
	pluginName = "Bento-Scans Link Retreiver"
	tableKey = "irc-irh"
	dbName = settings.dbName

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	tableName = "MangaItems"

	feedUrls = ["http://bento-scans.mokkori.fr/XDCC/"]




	def getMainItems(self):
		# for item in items:
		# 	self.log.info( item)
		#

		self.log.info( "Loading Bento-Scans Main Feed")

		channel = "bentoscans"
		server = "irchighway"
		ret = []

		for url in self.feedUrls:
			page = self.wg.getpage(url)

			self.log.info("Processing itemList markup....")
			soup = bs4.BeautifulSoup(page)
			self.log.info("Done. Searching")

			contentDiv = soup.find("div", id="content")

			mainTable = contentDiv.find("table", class_="listtable")

			for row in mainTable.find_all("tr"):
				item = {}
				rowItems = row.find_all("td")
				if len(rowItems) == 5:
					botname, pkgNum, dummy_dlcnt, size, info = rowItems

					item["pkgNum"] = pkgNum.get_text().strip("#").strip()

					item["server"] = server
					item["channel"] = channel

					sizeText = size.get_text().strip()
					# Skip all files that have sizes in bytes (just header files and shit)
					if "b" in sizeText:
						continue

					if "K" in sizeText.upper():
						item["size"] = float(sizeText.upper().strip("K").strip())/1000.0
					else:
						item["size"] = float(sizeText.upper().strip("M").strip())

					item["botName"] = botname.get_text().strip()
					item["fName"] = info.get_text().strip()

					# I'm using the filename+botname for the unique key to the database.
					itemKey = item["fName"]+item["botName"]

					item = json.dumps(item)

					ret.append((itemKey, item))
				# else:
				# 	print("Bad row? ", row)

				if not runStatus.run:
					self.log.info( "Breaking due to exit flag being set")
					break


		self.log.info("All data loaded")
		return ret

def test():
	loader = BentoTriggerLoader()
	ret = loader.go()
	# print(ret)

if __name__ == "__main__":
	import utilities.testBase
	with utilities.testBase.testSetup():
		test()

