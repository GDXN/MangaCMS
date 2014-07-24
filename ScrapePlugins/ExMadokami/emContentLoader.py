
import webFunctions
import settings
import os
import os.path

import nameTools as nt

import time

import urllib.parse
import re
import runStatus
import traceback
import bs4

import ScrapePlugins.RetreivalDbBase


import archCleaner

class EmContentLoader(ScrapePlugins.RetreivalDbBase.ScraperDbBase):


	archCleaner = archCleaner.ArchCleaner()

	wg = webFunctions.WebGetRobust()
	loggerPath = "Main.Em.Cl"
	pluginName = "Exhen.Madokami Content Retreiver"
	tableKey = "em"
	dbName = settings.dbName

	urlBase = "http://exhen.madokami.com/"
	tableName = "HentaiItems"

	def retreiveTodoLinksFromDB(self):

		self.log.info( "Fetching items from db...",)

		rows = self.getRowsByValue(dlState=0)

		self.log.info( "Done")
		if not rows:
			self.log.info("No new items, nothing to do.")
			return


		items = []
		for item in rows:

			item["retreivalTime"] = time.gmtime(item["retreivalTime"])


			seriesName = item["seriesName"]
			seriesName = seriesName.replace("[", "(").replace("]", "(")
			safeBaseName = nt.makeFilenameSafe(item["seriesName"])

			targetDir = os.path.join(settings.emSettings["dlDir"], safeBaseName.title())
			item["targetDir"] = targetDir
			if not os.path.exists(targetDir):
				try:
					os.makedirs(targetDir)
				except OSError:
					self.log.critical("Directory creation failed?")
					self.log.critical(traceback.format_exc())


			items.append(item)

		self.log.info( "Have %s new items to retreive in EmDownloader" % len(items))


		items = sorted(items, key=lambda k: k["retreivalTime"], reverse=True)
		return items

	def getFile(self, fileUrl, referrer):
		pgctnt, pghandle = self.wg.getpage(fileUrl, returnMultiple = True, addlHeaders={'Referer': referrer})
		hName = pghandle.info()['Content-Disposition'].split('filename=')[1]
		self.log.info( "HName: %s", hName, )
		self.log.info( "Size = %s", len(pgctnt))


		return pgctnt, hName



	def getLink(self, link):
		sourceUrl, originFileName = link["sourceUrl"], link["originName"]

		self.log.info( "Should retreive: %s, url - %s", originFileName, sourceUrl)

		itemId = sourceUrl.split(":")[-1]
		pageUrl = 'http://exhen.madokami.com/?action=gallery&id={id}&index=0'.format(id=itemId)
		downloadUrl = 'http://exhen.madokami.com/api.php?action=download&id={id}'.format(id=itemId)

		self.updateDbEntry(sourceUrl, dlState=1)
		# self.conn.commit()


		try:
			content, hName = self.getFile(downloadUrl, pageUrl)
		except:
			self.log.error("Unrecoverable error retreiving content %s", link)
			self.log.error("Traceback: %s", traceback.format_exc())

			self.updateDbEntry(sourceUrl, dlState=-1)
			return



		# And fix %xx crap
		hName = urllib.parse.unquote(hName)

		fName = nt.makeFilenameSafe(hName)

		fqFName = os.path.join(link["targetDir"], fName)
		self.log.info( "SaveName = %s", fqFName)


		fileName, ext = os.path.splitext(fName)
		loop = 1
		while os.path.exists(fqFName):
			fName = "%s (%d).%s" % (fileName, loop,  ext)
			fqFName = os.path.join(link["targetDir"], fName)
			loop += 1
		self.log.info( "Writing file")

		filePath, fileName = os.path.split(fqFName)

		try:
			with open(fqFName, "wb") as fp:
				fp.write(content)
		except TypeError:
			self.log.error("Failure trying to retreive content from source %s", sourceUrl)
			self.updateDbEntry(sourceUrl, dlState=-4, downloadPath=filePath, fileName=fileName)
			return
		#self.log.info( filePath)
		try:
			dedupState = self.archCleaner.processNewArchive(fqFName, deleteDups=True)
		except archCleaner.NotAnArchive:
			self.log.warning("File is not an archive!")
			self.log.warning("File '%s'", fqFName)
			dedupState = "not-an-archive"
		except archCleaner.DamagedArchive:
			self.log.warning("Corrupt Archive!")
			self.log.warning("Archive '%s'", fqFName)
			dedupState = "corrupt-archive"
			self.addTags(sourceUrl=sourceUrl, tags=dedupState)
			self.updateDbEntry(sourceUrl, dlState=-3, downloadPath=filePath, fileName=fileName)
			return

		self.log.info( "Done")
		self.addTags(sourceUrl=sourceUrl, tags=dedupState)
		self.updateDbEntry(sourceUrl, dlState=2, downloadPath=filePath, fileName=fileName)
		return


	def fetchLinkList(self, linkList):
		try:
			for link in linkList:
				if link is None:
					self.log.error("One of the items in the link-list is none! Wat?")
					continue

				ret = self.getLink(link)
				if ret == "Limited":
					break


				if not runStatus.run:
					self.log.info( "Breaking due to exit flag being set")
					break


		except:
			self.log.critical("Exception!")
			traceback.print_exc()
			self.log.critical(traceback.format_exc())


	def processTodoLinks(self, links):
		if links:
			# Multi-threading goes here if I want it.
			self.fetchLinkList(links)

	def go(self):

		todo = self.retreiveTodoLinksFromDB()
		if not runStatus.run:
			return
		self.processTodoLinks(todo)
