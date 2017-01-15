
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


import processDownload

class JzContentLoader(ScrapePlugins.RetreivalDbBase.ScraperDbBase):




	loggerPath = "Main.Manga.Jz.Cl"
	pluginName = "Japanzai Content Retreiver"
	tableKey = "jz"
	dbName = settings.DATABASE_DB_NAME

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	urlBase = "http://download.japanzai.com/"

	tableName = "MangaItems"

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
			safeBaseName = nt.makeFilenameSafe(item["seriesName"])



			if seriesName in nt.dirNameProxy:
				self.log.info( "Have target dir for '%s' Dir = '%s'", seriesName, nt.dirNameProxy[seriesName]['fqPath'])
				item["targetDir"] = nt.dirNameProxy[seriesName]["fqPath"]
			else:
				self.log.info( "Don't have target dir for: %s Using default for: %s, full name = %s", seriesName, item["seriesName"], item["originName"])
				targetDir = os.path.join(settings.jzSettings["dirs"]['mDlDir'], safeBaseName)
				if not os.path.exists(targetDir):
					try:
						os.makedirs(targetDir)
						item["targetDir"] = targetDir
						self.updateDbEntry(item["sourceUrl"],flags=" ".join([item["flags"], "newdir"]))
						self.conn.commit()

						self.conn.commit()
					except OSError:
						self.log.critical("Directory creation failed?")
						self.log.critical(traceback.format_exc())
				else:
					self.log.warning("Directory not found in dir-dict, but it exists!")
					self.log.warning("Directory-Path: %s", targetDir)
					item["targetDir"] = targetDir

					self.updateDbEntry(item["sourceUrl"],flags=" ".join([item["flags"], "haddir"]))
					self.conn.commit()

			items.append(item)

		self.log.info( "Have %s new items to retreive in JzDownloader" % len(items))


		items = sorted(items, key=lambda k: k["retreivalTime"], reverse=True)
		return items



	def getDownloadUrl(self, containerUrl):
		page = self.wg.getpage(containerUrl)
		soup = bs4.BeautifulSoup(page, "lxml")

		link = soup.find("a", {"id": "dlButton"})
		if link:
			quotedFilename = urllib.parse.quote(link["href"])
			url = urllib.parse.urljoin(containerUrl, quotedFilename)
			return url

		return None


	def getLinkFile(self, fileUrl, refUrl):
		pgctnt, pghandle = self.wg.getpage(fileUrl, returnMultiple = True, addlHeaders={'Referer': refUrl})
		pageUrl = pghandle.geturl()
		hName = urllib.parse.urlparse(pageUrl)[2].split("/")[-1]
		self.log.info( "HName: %s", hName, )
		self.log.info( "Size = %s", len(pgctnt))


		return pgctnt, hName


	def getLink(self, link):
		sourceUrl, originFileName = link["sourceUrl"], link["originName"]

		self.log.info( "Should retreive: %s, url - %s", originFileName, sourceUrl)

		self.updateDbEntry(sourceUrl, dlState=1)
		self.conn.commit()

		fileUrl = self.getDownloadUrl(sourceUrl)
		if fileUrl is None:
			self.log.warning("Could not find url!")
			self.deleteRowsByValue(sourceUrl=sourceUrl)
			return


		try:
			content, hName = self.getLinkFile(fileUrl, sourceUrl)
		except:
			self.log.error("Unrecoverable error retreiving content %s", link)
			self.log.error("Traceback: %s", traceback.format_exc())

			self.updateDbEntry(sourceUrl, dlState=-1)
			return

		# print("Content type = ", type(content))


		# And fix %xx crap
		hName = urllib.parse.unquote(hName)

		fName = "%s - %s" % (originFileName, hName)
		fName = nt.makeFilenameSafe(fName)

		fqFName = os.path.join(link["targetDir"], fName)
		self.log.info( "SaveName = %s", fqFName)


		loop = 1
		while os.path.exists(fqFName):
			fName = "%s - (%d) - %s" % (originFileName, loop,  hName)
			fqFName = os.path.join(link["targetDir"], fName)
			loop += 1
		self.log.info( "Writing file")

		filePath, fileName = os.path.split(fqFName)

		try:
			with open(fqFName, "wb") as fp:
				fp.write(content)
		except TypeError:
			self.log.error("Failure trying to retreive content from source %s", sourceUrl)
			return
		#self.log.info( filePath)

		dedupState = processDownload.processDownload(link["seriesName"], fqFName, deleteDups=True, includePHash=True)
		self.log.info( "Done")

		self.updateDbEntry(sourceUrl, dlState=2, downloadPath=filePath, fileName=fileName, tags=dedupState)
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

			# Multithreading goes here, if I decide I want it at some point
			self.fetchLinkList(links)


	def go(self):

		todo = self.retreiveTodoLinksFromDB()
		if not runStatus.run:
			return
		self.processTodoLinks(todo)
