
import webFunctions
import settings
import os
import os.path

import nameTools as nt

import time
import random
import urllib.parse
import re
import sys
import runStatus
import traceback
import bs4

import ScrapePlugins.RetreivalDbBase

from concurrent.futures import ThreadPoolExecutor

import archCleaner

class MkContentLoader(ScrapePlugins.RetreivalDbBase.ScraperDbBase):


	archCleaner = archCleaner.ArchCleaner()

	wg = webFunctions.WebGetRobust(creds=[("http://manga.madokami.com", settings.mkSettings["login"], settings.mkSettings["passWd"])])
	loggerPath = "Main.Mk.Cl"
	pluginName = "Manga.Madokami Content Retreiver"
	tableKey = "mk"
	dbName = settings.dbName

	retreivalThreads = 2

	tableName = "MangaItems"
	urlBase = "http://manga.madokami.com/"

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



			if seriesName in nt.dirNameProxy:
				# self.log.info( "Have target dir for '%s' Dir = '%s'", seriesName, nt.dirNameProxy[seriesName]['fqPath'])
				item["targetDir"] = nt.dirNameProxy[seriesName]["fqPath"]
			else:
				self.log.info( "Don't have target dir for: %s Using default for: %s, full name = %s", seriesName, item["seriesName"], item["originName"])
				if "picked" in item["flags"]:
					targetDir = os.path.join(settings.jzSettings["dirs"]['mnDir'], safeBaseName)
				else:
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
		soup = bs4.BeautifulSoup(page)

		link = soup.find("a", {"id": "dlButton"})
		if link:
			quotedFilename = urllib.parse.quote(link["href"])
			url = urllib.parse.urljoin(containerUrl, quotedFilename)
			return url

		return None


	def getLinkFile(self, fileUrl):
		pgctnt, pghandle = self.wg.getpage(fileUrl, returnMultiple = True, addlHeaders={'Referer': "http://manga.madokami.com"})
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
			content, hName = self.getLinkFile(sourceUrl)
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
			self.updateDbEntry(sourceUrl, dlState=-4, downloadPath=filePath, fileName=fileName)
			return
		#self.log.info( filePath)

		ext = os.path.splitext(fileName)[-1]
		imageExts = ["jpg", "png", "bmp"]
		if not any([ext.endswith(ex) for ex in imageExts]):
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
				self.updateDbEntry(sourceUrl, dlState=-3, downloadPath=filePath, fileName=fileName, tags=dedupState)
				return
		else:
			dedupState = ""

		self.log.info( "Done")
		self.updateDbEntry(sourceUrl, dlState=2, downloadPath=filePath, fileName=fileName, tags=dedupState)
		return


	def fetchLinkList(self, linkList):

		# Muck about in the webget internal settings
		self.wg.errorOutCount = 4
		self.wg.retryDelay    = 5

		try:
			for link in linkList:
				if link is None:
					self.log.error("One of the items in the link-list is none! Wat?")
					continue

				delay = random.randint(5, 10)
				for x in range(delay):
					time.sleep(1)
					remaining = delay-x
					sys.stdout.write("\rMk CL sleeping %d       " % remaining)
					sys.stdout.flush()
					if not runStatus.run:
						self.log.info("Breaking due to exit flag being set")
						return

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

			def iter_baskets_from(items, maxbaskets=3):
				'''generates evenly balanced baskets from indexable iterable'''
				item_count = len(items)
				baskets = min(item_count, maxbaskets)
				for x_i in range(baskets):
					yield [items[y_i] for y_i in range(x_i, item_count, baskets)]

			linkLists = iter_baskets_from(links, maxbaskets=self.retreivalThreads)

			with ThreadPoolExecutor(max_workers=self.retreivalThreads) as executor:

				for linkList in linkLists:
					executor.submit(self.fetchLinkList, linkList)

				executor.shutdown(wait=True)


	def go(self):

		todo = self.retreiveTodoLinksFromDB()
		if not runStatus.run:
			return
		self.processTodoLinks(todo)
