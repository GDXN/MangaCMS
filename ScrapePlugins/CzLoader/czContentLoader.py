
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

import zipfile
import hashlib


class CzContentLoader(ScrapePlugins.RetreivalDbBase.ScraperDbBase):


	wg = webFunctions.WebGetRobust()
	loggerPath = "Main.Cz.Cl"
	pluginName = "Crazy's Manga Content Retreiver"
	tableKey = "cz"
	dbName = settings.dbName
	urlBase = "http://crazytje.be/Scanlation"

	def retreiveTodoLinksFromDB(self):

		self.log.info( "Fetching items from db...",)

		rows = self.getRowsByValue(dlState=0)

		self.log.info( "Done")
		if not rows:
			return

		items = []

		for item in rows:

			item["retreivalTime"] = time.gmtime(item["retreivalTime"])


			baseNameLower = nt.sanitizeString(item["seriesName"])
			safeBaseName = nt.makeFilenameSafe(item["seriesName"])



			if baseNameLower in nt.dirNameProxy:
				self.log.info( "Have target dir for '%s' Dir = '%s'", baseNameLower, nt.dirNameProxy[baseNameLower]['fqPath'])
				item["targetDir"] = nt.dirNameProxy[baseNameLower]["fqPath"]
			else:
				self.log.info( "Don't have target dir for: %s Using default for: %s, full name = %s", baseNameLower, item["seriesName"], item["originName"])
				targetDir = os.path.join(settings.czSettings["dirs"]['mDlDir'], safeBaseName)

				if not os.path.exists(targetDir):
					try:
						self.log.info("Creating directory!")
						os.makedirs(targetDir)
						item["targetDir"] = targetDir
						self.updateDbEntry(item["sourceUrl"],flags=" ".join([item["flags"], "newdir"]))
						self.conn.commit()

						# Since we created a new directory in the downloads folder, update the directory
						# lookup tool. Force the rescan, since the update rate is limited normally
						nt.dirNameProxy.forceUpdateContainingPath(targetDir)

					except OSError:
						self.log.critical("Directory creation failed?")
						self.log.critical(traceback.format_exc())
				else:
					self.log.warning("Directory not found in dir-dict, but it exists! Maybe it was just created?")
					self.log.warning("Directory-Path: %s", targetDir)


					item["targetDir"] = targetDir

					self.updateDbEntry(item["sourceUrl"],flags=" ".join([item["flags"], "haddir"]))
					self.conn.commit()

			items.append(item)


		self.log.info( "Have %s new items to retreive in CzDownloader" % len(items))

		items = sorted(items, key=lambda k: k["retreivalTime"], reverse=True)
		return items



	def getDownloadUrl(self, containerUrl, fileName):
		soup = self.wg.getpage(containerUrl, soup=True)

		table = soup.find("table", id="tablesorter")
		rows = table.tbody.find_all("tr")

		link = None
		for row in rows:
			if fileName in row.get_text():
				link = row.find("td", class_="download").a



		if link:
			return link["href"]

		self.log.error("No download for file %s on page %s", fileName, containerUrl)
		return None

	def getLinkFile(self, fileUrl):
		pgctnt, pghandle = self.wg.getpage(fileUrl, returnMultiple = True)
		hName = pghandle.info()['Content-Disposition'].split('filename=')[1]
		self.log.info( "HName: %s", hName, )
		self.log.info( "Size = %s", len(pgctnt))

		return pgctnt, hName


	def getLink(self, link):
		sourceUrl, originFileName = link["sourceUrl"], link["originName"]

		sourceUrl, sourceFn = sourceUrl.split("#")

		self.log.info( "Should retreive: %s, %s, url - %s", originFileName, originFileName==sourceFn, sourceUrl)


		self.updateDbEntry(link["sourceUrl"], dlState=1)
		self.conn.commit()

		if originFileName != sourceFn:
			self.log.error("Non matching filenames = '%s' - '%s'", originFileName, sourceFn)
			self.updateDbEntry(link["sourceUrl"], dlState=-1)
			raise ValueError("wat? Filenames do not match!")


		fileUrl = self.getDownloadUrl(sourceUrl, sourceFn)
		if fileUrl is None:
			self.log.warning("Could not find url!")
			# self.deleteRowsByValue(sourceUrl=sourceUrl)
			return

		self.log.info("Found download URL = %s", fileUrl)

		try:
			content, hName = self.getLinkFile(fileUrl)
		except:
			self.log.error("Unrecoverable error retreiving content %s", link)
			self.log.error("Traceback: %s", traceback.format_exc())

			self.updateDbEntry(link["sourceUrl"], dlState=-1)
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


		self.log.info( "Done")

		self.updateDbEntry(link["sourceUrl"], dlState=2, downloadPath=filePath, fileName=fileName)
		return


	def fetchLinkList(self, linkList):
		try:
			for link in linkList:
				if link is None:
					self.log.error("One of the items in the link-list is none! Wat?")
					continue

				self.getLink(link)


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
