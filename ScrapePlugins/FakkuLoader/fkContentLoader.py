
# -*- coding: utf-8 -*-

import webFunctions
import os
import os.path

import random
import sys
import zipfile
import nameTools as nt

import runStatus
import time
import urllib.request, urllib.parse, urllib.error
import traceback

import settings
import bs4
import re

import archCleaner
import json
from concurrent.futures import ThreadPoolExecutor

import ScrapePlugins.RetreivalDbBase

class FakkuContentLoader(ScrapePlugins.RetreivalDbBase.ScraperDbBase):

	archCleaner = archCleaner.ArchCleaner()

	wg = webFunctions.WebGetRobust()

	dbName = settings.dbName
	loggerPath = "Main.Fakku.Cl"
	pluginName = "Fakku Content Retreiver"
	tableKey   = "fk"
	urlBase = "http://www.fakku.net/"

	tableName = "HentaiItems"


	retreivalThreads = 6


	def go(self):

		newLinks = self.retreiveTodoLinksFromDB()
		if newLinks:
			self.processTodoLinks(newLinks)

	def retreiveTodoLinksFromDB(self):

		self.log.info("Fetching items from db...",)

		rows = self.getRowsByValue(dlState=0)
		if not rows:
			self.log.info("No items")
			return
		self.log.info("Done")
		# print(rows)
		items = []
		for row in rows:
			# self.log.info("Row = %s", row)

			# Wait 18 hours after an item is uploaded to actually scrape it, since it looks like uploads
			# are almost always in a fucked up order at the start
			# Seriously, these kind of things are sequentially numbered. How can you fuck that up?
			# They manage, somehow.
			if row["retreivalTime"] < (time.time() + 60*60*18):
				items.append(row)  # Actually the contentID
		self.log.info("Have %s new items to retreive in FakkuDownloader" % len(items))

		return items



	def processTodoLinks(self, links):
		if links:

			def iter_baskets_from(items, maxbaskets=3):
				'''generates evenly balanced baskets from indexable iterable'''
				item_count = len(items)
				baskets = min(item_count, maxbaskets)
				for x_i in range(baskets):
					yield [items[y_i] for y_i in range(x_i, item_count, baskets)]

			linkLists = iter_baskets_from(links, maxbaskets=self.retreivalThreads)

			with ThreadPoolExecutor(max_workers=self.retreivalThreads) as executor:

				for linkList in linkLists:
					fut = executor.submit(self.downloadItemsFromList, linkList)

				executor.shutdown(wait=True)




	def downloadItemsFromList(self, linkList):


		for contentId in linkList:

			try:
				dlDict = self.processDownloadInfo(contentId)
				ret = self.doDownload(dlDict)
				if ret:
					delay = random.randint(5, 30)
				else:
					delay = 0

			except:
				print("ERROR WAT?")
				traceback.print_exc()
				delay = 1


			for x in range(delay):
				time.sleep(1)
				remaining = delay-x
				sys.stdout.write("\rFakku CL sleeping %d          " % remaining)
				sys.stdout.flush()
				if not runStatus.run:
					self.log.info("Breaking due to exit flag being set")
					return
			if not runStatus.run:
				self.log.info("Breaking due to exit flag being set")
				return

	def processDownloadInfo(self, linkDict):

		self.updateDbEntry(linkDict["sourceUrl"], dlState=1)

		sourcePage = linkDict["sourceUrl"]
		category   = linkDict['seriesName']

		self.log.info("Retreiving item: %s", sourcePage)

		linkDict['dirPath'] = os.path.join(settings.fkSettings["dlDir"], nt.makeFilenameSafe(category))

		if not os.path.exists(linkDict["dirPath"]):
			os.makedirs(linkDict["dirPath"])
		else:
			self.log.info("Folder Path already exists?: %s", linkDict["dirPath"])

		self.log.info("Folderpath: %s", linkDict["dirPath"])

		self.log.debug("Linkdict = ")
		for key, value in list(linkDict.items()):
			self.log.debug("		%s - %s", key, value)


		return linkDict


	def doDownload(self, linkDict):


		images = []
		containerUrl = linkDict["sourceUrl"]+"/read"

		if "http://www.fakku.net/videos/" in containerUrl:
			self.log.warning("Cannot download video items.")
			self.updateDbEntry(linkDict["sourceUrl"], dlState=-5, downloadPath="Video", fileName="ERROR: Video", lastUpdate=time.time())
			return False

		if "http://www.fakku.net/games/" in containerUrl:
			self.log.warning("Cannot download game items.")
			self.updateDbEntry(linkDict["sourceUrl"], dlState=-6, downloadPath="Game", fileName="ERROR: Game", lastUpdate=time.time())
			return False


		imagePage = self.wg.getpage(containerUrl, addlHeaders={'Referer': linkDict["sourceUrl"]})

		if "This content has been disabled due to a DMCA takedown notice, it is no longer available to download or read online in your region." in imagePage:
			self.log.warning("Assholes have DMCAed this item. Not available anymore.")
			self.updateDbEntry(linkDict["sourceUrl"], dlState=-4, downloadPath="DMCA", fileName="ERROR: DMCAed", lastUpdate=time.time())
			return False

		# So...... Fakku's reader is completely javascript driven. No (easily) parseable shit here.
		# Therefore: WE DECEND TO THE LEVEL OF REGEXBOMINATIONS!
		pathFormatterRe = re.compile(r"return '(https://t\.fakku\.net/images/.+/.+/.+?/images/)' \+ x \+ '(\.jpg)';", re.IGNORECASE)

		# We need to know how many images there are, but there is no convenient way to access this information.
		# The fakku code internally uses the length of the thumbnail array for the number of images, so
		# we extract that array, parse it (since it's javascript, variables are JSON, after all), and
		# just look at the length ourselves as well.
		thumbsListRe    = re.compile(r"window\.params\.thumbs = (\[.+?\]);", re.IGNORECASE)

		thumbs        = thumbsListRe.search(imagePage)
		pathFormatter = pathFormatterRe.search(imagePage)
		# print("Thumbs = ", thumbs.group(1))
		prefix, postfix = pathFormatter.group(1), pathFormatter.group(2)

		prefix = prefix.encode("ascii").decode("utf-8")
		postfix = postfix.encode("ascii").decode("utf-8")

		print("pathFormatter = ", prefix, prefix)

		if not thumbs and pathFormatter:
			self.log.error("Could not find items on page!")
			self.log.error("URL: '%s'", containerUrl)

		items = json.loads(thumbs.group(1))

		# for item in items:
		# 	print("Item = ", item)


		imageUrls = []
		for x in range(len(items)):
			item = '{prefix}{num:03d}{postfix}'.format(prefix=pathFormatter.group(1), num=x+1, postfix=pathFormatter.group(2))
			imageUrls.append(item)

		# print("Prepared image URLs = ")
		# print(imageUrls)

		# print(linkDict)

		images = []
		for imageUrl in imageUrls:

			imagePath = urllib.parse.urlsplit(imageUrl)[2]
			imageFileName = imagePath.split("/")[-1]
			imageData = self.wg.getpage(imageUrl, addlHeaders={'Referer': containerUrl})

			images.append((imageFileName, imageData))
			# Find next page


		# self.log.info(len(content))

		if images:
			fileN = linkDict["originName"]+".zip"
			fileN = nt.makeFilenameSafe(fileN)


			# self.log.info("geturl with processing", fileN)
			wholePath = os.path.join(linkDict["dirPath"], fileN)
			self.log.info("Complete filepath: %s", wholePath)

					#Write all downloaded files to the archive.
			arch = zipfile.ZipFile(wholePath, "w")
			for imageName, imageContent in images:
				arch.writestr(imageName, imageContent)
			arch.close()


			self.log.info("Successfully Saved to path: %s", wholePath)

			if not linkDict["tags"]:
				linkDict["tags"] = ""


			dedupState = self.archCleaner.processNewArchive(wholePath, deleteDups=True, includePHash=True)
			self.log.info( "Done")

			if dedupState:
				self.addTags(sourceUrl=linkDict["sourceUrl"], tags=dedupState)

			self.updateDbEntry(linkDict["sourceUrl"], dlState=2, downloadPath=linkDict["dirPath"], fileName=fileN, lastUpdate=time.time())

			self.conn.commit()
			return wholePath

		else:

			self.updateDbEntry(linkDict["sourceUrl"], dlState=-1, downloadPath="ERROR", fileName="ERROR: FAILED", lastUpdate=time.time())

			self.conn.commit()
			return False
