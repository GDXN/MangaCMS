
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
import urllib.error

import processDownload

class SkContentLoader(ScrapePlugins.RetreivalDbBase.ScraperDbBase):

	loggerPath = "Main.Sk.Cl"
	pluginName = "Starkana Content Retreiver"
	tableKey = "sk"
	dbName = settings.dbName
	urlBase = "http://starkana.com/"

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	tableName = "MangaItems"

	def retreiveTodoLinksFromDB(self):

		self.log.info( "Fetching items from db...",)

		rows = self.getRowsByValue(dlState=0)

		self.log.info( "Done")
		if not rows:
			return

		# I'm not totally sure how starkana's rate-limiting works.
		# I thought it was total transfered/day at first, but
		# I think they may now have a system that looks at shorter
		# term transfer totals, and then triggers a 24 hour ban
		# if you exceed a limit or something
		# Anyways, limit the maximum items/hour to 50 items
		rows = rows[:50]

		items = []
		for item in rows:

			item["retreivalTime"] = time.gmtime(item["retreivalTime"])


			baseNameLower = nt.prepFilenameForMatching(item["seriesName"])
			safeBaseName = nt.makeFilenameSafe(item["seriesName"])



			if baseNameLower in nt.dirNameProxy:
				self.log.info( "Have target dir for '%s' Dir = '%s'", baseNameLower, nt.dirNameProxy[baseNameLower]['fqPath'])
				item["targetDir"] = nt.dirNameProxy[baseNameLower]["fqPath"]
			else:
				self.log.info( "Don't have target dir for: %s Using default for: %s, full name = %s", baseNameLower, item["seriesName"], item["originName"])
				if "picked" in item["flags"]:
					targetDir = os.path.join(settings.skSettings["dirs"]['mnDir'], safeBaseName)
				else:
					targetDir = os.path.join(settings.skSettings["dirs"]['mDlDir'], safeBaseName)
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

		self.log.info( "Have %s new items to retreive in SkDownloader", len(items))


		items = sorted(items, key=lambda k: k["retreivalTime"], reverse=True)
		return items



	def getDownloadUrl(self, containerUrl):
		page = self.wg.getpage(containerUrl)
		soup = bs4.BeautifulSoup(page)

		link = soup.find("a", href=re.compile(".*download.*"))

		if link:
			return link["href"]

		return None

	def getLinkFile(self, fileUrl):
		pgctnt, pghandle = self.wg.getpage(fileUrl, returnMultiple = True)
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
		try:
			fileUrl = self.getDownloadUrl(sourceUrl)
		except urllib.error.URLError:
			self.log.error("Unrecoverable error retreiving content %s", link)
			self.log.error("Traceback: %s", traceback.format_exc())

			self.updateDbEntry(sourceUrl, dlState=-1)
			return


		if fileUrl is None:
			self.log.warning("Could not find url!")
			self.deleteRowsByValue(sourceUrl=sourceUrl)
			return

		if fileUrl == "http://starkana.com/download/manga/":
			self.log.warning("File doesn't actually exist because starkana are a bunch of douchecanoes!")
			self.deleteRowsByValue(sourceUrl=sourceUrl)
			return

		try:
			content, hName = self.getLinkFile(fileUrl)
		except:
			self.log.error("Unrecoverable error retreiving content %s", link)
			self.log.error("Traceback: %s", traceback.format_exc())

			self.updateDbEntry(sourceUrl, dlState=-1)
			return

		# print("Content type = ", type(content))

		# Clean Annoying, bullshit self-promotion in names
		hName = hName.replace("[starkana.com]_", "").replace("[starkana.com]", "")

		# And fix %xx crap
		hName = urllib.parse.unquote(hName)

		fName = "%s - %s" % (originFileName, hName)
		fName = nt.makeFilenameSafe(fName)

		fqFName = os.path.join(link["targetDir"], fName)

		fqFName, ext = os.path.splitext(fqFName)
		fqFName = "%s [Starkana]%s" % (fqFName, ext)


		self.log.info( "SaveName = %s", fqFName)

		loop = 1
		while os.path.exists(fqFName):
			fqFName, ext = os.path.splitext(fqFName)
			fqFName = "%s (%d)%s" % (fqFName, loop,  ext)
			loop += 1
		self.log.info( "Writing file")

		filePath, fileName = os.path.split(fqFName)

		if type(content) is str and "You have been limit reached." in content:
			self.log.warning("Hit rate-limiting error. Breaking")
			self.updateDbEntry(sourceUrl, dlState=0)
			return "Limited"

		try:
			with open(fqFName, "wb") as fp:
				fp.write(content)
		except TypeError:
			self.log.error("Failure trying to retreive content from source %s", sourceUrl)
			return
		#self.log.info( filePath)

		dedupState = processDownload.processDownload(link["seriesName"], fqFName, deleteDups=True)
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
