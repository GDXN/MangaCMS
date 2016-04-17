


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




	loggerPath = "Main.Manga.XdP.Fl"
	pluginName = "Xdcc-Parser based site Link Retreiver"
	tableKey = "irc-irh"
	dbName = settings.DATABASE_DB_NAME

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	tableName = "MangaItems"

	# Feeds are ({xdcc list}, {IRC Channel})
	feedUrls = [
		('http://bento-scans.mokkori.fr/XDCC/',                         'bentoscans'),
		('http://mangaichiscans.mokkori.fr/XDCC/',                      'msd'),
		('http://www.ipitydafoo.com/at2/xdccparser.py?bot=01',          'deadbeat'),            # Azrael
		('http://www.ipitydafoo.com/at2/xdccparser.py?bot=02',          'aerandria'),           # Boink
		('http://www.ipitydafoo.com/at2/xdccparser.py?bot=03',          'a-team'),              # Death
		('http://www.ipitydafoo.com/at2/xdccparser.py?bot=04',          'a-team'),              # Hannibal
		('http://www.mudascantrad.tk/packlist_mh/xdccparser.py?bot=01', 'mto-group'),           # emma-chan
		]


	def getMainItems(self):
		# for item in items:
		# 	self.log.info( item)
		#

		self.log.info( "Loading XdccParser Feeds")


		server = "irchighway"
		ret = []

		for url, channel in self.feedUrls:
			page = self.wg.getpage(url)

			self.log.info("Processing itemList markup....")
			soup = bs4.BeautifulSoup(page, "lxml")
			self.log.info("Done. Searching")

			contentDiv = soup.find("div", id="content")

			mainTable = contentDiv.find("table", class_="listtable")
			new = 0
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
					new += 1
				# else:
				# 	print("Bad row? ", row)

				if not runStatus.run:
					self.log.info( "Breaking due to exit flag being set")
					break

			self.log.info("Found %s items on page!", new)

		self.log.info("All data loaded")
		return ret

def test():
	loader = TriggerLoader()
	ret = loader.go()
	# print(ret)

if __name__ == "__main__":
	import utilities.testBase
	with utilities.testBase.testSetup():
		test()

