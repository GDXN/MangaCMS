
import feedparser
import webFunctions
import bs4
import re

import urllib.parse
import urllib.error
import time
import dateutil.parser
import runStatus
import settings
import datetime
import json

import ScrapePlugins.RetreivalDbBase
import nameTools as nt

class EmFeedLoader(ScrapePlugins.RetreivalDbBase.ScraperDbBase):


	wg = webFunctions.WebGetRobust()
	loggerPath = "Main.Em.Fl"
	pluginName = "Exhen.Madokami Link Retreiver"
	tableKey = "em"
	dbName = settings.dbName

	urlBase = "http://exhen.madokami.com/"

	tableName = "HentaiItems"
	def checkLogin(self):
		pass

	def closeDB(self):
		self.log.info( "Closing DB...",)
		self.conn.close()
		self.log.info( "done")

	def getApiItems(self, page=0):

		apiPage = 'http://exhen.madokami.com/api.php?search=&page={page}&order=posted&action=galleries'.format(page=page)
		try:
			feed = self.wg.getpage(apiPage, addlHeaders={'Referer': self.urlBase})
		except urllib.error.URLError:
			self.log.error("Could not fetch page '%s'", apiPage)
			return []

		try:
			feed = feed.decode("utf-8")
			data = json.loads(feed)
			self.log.info("done")
		except ValueError:
			self.log.critical("Get did not return JSON like normal!")
			self.log.critical("Returned page contents = %s", feed)
			return []
		if not data['ret'] == True:
			self.log.error("API Request failed!")
			return[]

		if not "data" in data and "galleries" in data["data"]:
			self.log.error("No galleries on requested page!")
			return []

		ret = []

		for gallery in data["data"]["galleries"]:
			# print("Item = ", gallery)

			tags = gallery["tags"]
			if not "language" in tags or not "english" in tags["language"]:
				self.log.info("Item is not english. Skipping.")
				continue


			tagKeys = [
					['artist',    'artist'],
					['character', 'character'],
					['group',     'group',],
					['male',      '',],
					['misc',      '',],
					['parody',    'parody',],
					['female',    '',]
				]


			tagsExtracted = []
			for key, prefix in tagKeys:
				if key in tags:
					for value in tags[key]:
						tag = "%s %s" % (prefix, value)
						tag = tag.strip()
						while "  " in tag:
							tag = tag.replace("  ", " ")
						tag = tag.replace(" ", "-")
						tagsExtracted.append(tag)
			tagsExtracted = set(tagsExtracted)

			item = {}

			item["tags"] = ' '.join(tagsExtracted)


			# No yaoi, please
			if "yaoi" in item["tags"]:
				self.log.info("Yaoi. Do not want.")
				continue

			item["itemType"] = "None"
			if 'type' in gallery:
				item["itemType"] = gallery['type']

			if "origtitle" in gallery:
				item["note"] = "Original Title = {title}".format(title=gallery["origtitle"])

			item['dlLink'] = "exhen.madokami:{itemId}".format(itemId=gallery['id'])
			item["dlName"] = gallery['name']
			addDate = dateutil.parser.parse(gallery['updated'])
			item["date"] = time.mktime(addDate.timetuple())

			ret.append(item)
		# print(data)
		return ret


	def getMainItems(self):
		# for item in items:
		# 	self.log.info( item)
		#

		self.log.info( "Loading Madokami Main Feed")

		items = []


		items = self.getApiItems()

		return items




	def processLinksIntoDB(self, linksDicts):

		self.log.info( "Inserting...",)
		newItems = 0
		for link in linksDicts:
			if link is None:
				print("linksDicts", linksDicts)
				print("WAT")

			rows = self.getRowsByValue(originName  = link["dlName"])    #We only look at filenames to determine uniqueness,
			if not rows:
				newItems += 1


				self.insertIntoDb(retreivalTime   = link["date"],
									sourceUrl     = link["dlLink"],
									originName    = link["dlName"],
									dlState       = 0,
									seriesName    = link["itemType"],
									tags          = link["tags"],
									note          = link["note"],
									flags         = '')
				# Flags has to be an empty string, because the DB is annoying.
				# TL;DR, comparing with LIKE in a column that has NULLs in it is somewhat broken.


				self.log.info("New item: %s", (link["date"], link["dlLink"], link["itemType"], link["dlName"]))


			else:
				pass


		self.log.info( "Done")
		self.log.info( "Committing...",)
		self.conn.commit()
		self.log.info( "Committed")

		return newItems


	def go(self):

		self.resetStuckItems()
		self.log.info("Getting feed items")

		feedItems = self.getMainItems()
		self.log.info("Processing feed Items")

		self.processLinksIntoDB(feedItems)
		self.log.info("Complete")


