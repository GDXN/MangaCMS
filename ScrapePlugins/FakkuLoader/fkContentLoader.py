
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
		self.log.info("Have %s new items to retreive in PururinDownloader" % len(items))

		return items


	def processTodoLinks(self, inLinks):

		for contentId in inLinks:
			print("Loopin!")
			try:
				dlDict = self.processDownloadInfo(contentId)
				self.doDownload(dlDict)


				delay = random.randint(5, 30)
			except:
				print("ERROR WAT?")
				traceback.print_exc()
				delay = 1


			for x in range(delay):
				time.sleep(1)
				remaining = delay-x
				sys.stdout.write("\rPururin CL sleeping %d          " % remaining)
				sys.stdout.flush()
				if not runStatus.run:
					self.log.info("Breaking due to exit flag being set")
					return


	def processDownloadInfo(self, linkDict):

		self.updateDbEntry(linkDict["sourceUrl"], dlState=1)

		sourcePage = linkDict["sourceUrl"]
		category   = linkDict['seriesName']

		self.log.info("Retreiving item: %s", sourcePage)

		linkDict['dirPath'] = os.path.join(settings.puSettings["dlDir"], nt.makeFilenameSafe(category))

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

		imagePage = self.wg.getpage(containerUrl, addlHeaders={'Referer': linkDict["sourceUrl"]})

		with open("tmp.html", "wb") as fp:
			fp.write(imagePage.encode("utf-8"))

		# So...... Fakku's reader is completely javascript driven. No parseable shit here.
		# Therefore: WE DECEND TO THE LEVEL OF REGEXBOMINATIONS!
		pathFormatterRe = re.compile(r"return '(https://t.fakku.net/images/\w+/\w+/.+?/images/)' \+ x \+ '(.jpg)';", re.IGNORECASE)

		# We need to know how many images there are, but there is no convenient way to access this information.
		# The fakku code internally uses the length of the thumbnail array for the number of images, so
		# we extract that array, parse it (since it's javascript, variables are JSON, after all), and
		# just look at the length ourselves as well.
		thumbsListRe    = re.compile(r"window.params.thumbs = (\[.+?\]);", re.IGNORECASE)

		thumbs        = thumbsListRe.search(imagePage)
		pathFormatter = pathFormatterRe.search(imagePage)
		# print("Thumbs = ", thumbs.group(1))
		# print("pathFormatter = ", pathFormatter.group(1), pathFormatter.group(2))

		if not thumbs and pathFormatter:
			self.log.error("Could not find items on page!")
			self.log.error("URL: '%s'", containerUrl)

		items = json.loads(thumbs.group(1))

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
