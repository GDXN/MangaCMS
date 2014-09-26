
import webFunctions
import settings
import os
import os.path

import nameTools as nt

import time

import urllib.parse
import html.parser
import zipfile
import runStatus
import traceback
import bs4
import re
import ScrapePlugins.RetreivalDbBase

from concurrent.futures import ThreadPoolExecutor

import processDownload

class CxContentLoader(ScrapePlugins.RetreivalDbBase.ScraperDbBase):



	loggerPath = "Main.Cx.Cl"
	pluginName = "CXC Scans Content Retreiver"
	tableKey = "cx"
	dbName = settings.dbName
	tableName = "MangaItems"

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	retreivalThreads = 2

	def retreiveTodoLinksFromDB(self):

		self.log.info( "Fetching items from db...",)

		rows = self.getRowsByValue(dlState=0)

		self.log.info( "Done")
		if not rows:
			return

		items = []
		for item in rows:

			item["retreivalTime"] = time.gmtime(item["retreivalTime"])


			items.append(item)

		self.log.info( "Have %s new items to retreive in BtDownloader" % len(items))


		items = sorted(items, key=lambda k: k["retreivalTime"], reverse=True)
		return items



	def getLinkFile(self, fileUrl):
		pgctnt, pghandle = self.wg.getpage(fileUrl, returnMultiple = True, addlHeaders={'Referer': "http://manga.cxcscans.com/directory/"})
		pageUrl = pghandle.geturl()
		hName = urllib.parse.urlparse(pageUrl)[2].split("/")[-1]
		self.log.info( "HName: %s", hName, )
		self.log.info( "Size = %s", len(pgctnt))


		return pgctnt, hName


	def getLink(self, link):
		sourceUrl  = link["sourceUrl"]
		seriesName = link["seriesName"]
		originFileName = link["originName"]

		self.updateDbEntry(sourceUrl, dlState=1)
		self.log.info("Downloading = '%s', '%s'", seriesName, originFileName)
		dlPath, newDir = self.locateOrCreateDirectoryForSeries(seriesName)

		if link["flags"] == None:
			link["flags"] = ""

		if newDir:
			self.updateDbEntry(sourceUrl, flags=" ".join([link["flags"], "haddir"]))
			self.conn.commit()



		try:
			content, headerName = self.getLinkFile(sourceUrl)
		except:
			self.log.error("Unrecoverable error retreiving content %s", link)
			self.log.error("Traceback: %s", traceback.format_exc())

			self.updateDbEntry(sourceUrl, dlState=-1)
			return



		headerName = urllib.parse.unquote(headerName)

		fName = "%s - %s" % (originFileName, headerName)
		fName = nt.makeFilenameSafe(fName)

		fName, ext = os.path.splitext(fName)
		fName = "%s [CXC Scans]%s" % (fName, ext)

		fqFName = os.path.join(dlPath, fName)
		self.log.info( "SaveName = %s", fqFName)


		loop = 1
		while os.path.exists(fqFName):
			fName, ext = os.path.splitext(fName)
			fName = "%s (%d)%s" % (fName, loop,  ext)
			fqFName = os.path.join(link["targetDir"], fName)
			loop += 1
		self.log.info("Writing file")



		filePath, fileName = os.path.split(fqFName)

		try:
			with open(fqFName, "wb") as fp:
				fp.write(content)
		except TypeError:
			self.log.error("Failure trying to retreive content from source %s", sourceUrl)
			self.updateDbEntry(sourceUrl, dlState=-4, downloadPath=filePath, fileName=fileName)
			return
		#self.log.info( filePath)



		dedupState = processDownload.processDownload(seriesName, fqFName, deleteDups=True)

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
