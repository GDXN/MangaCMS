
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
import ScrapePlugins.RetreivalBase


import processDownload

class ContentLoader(ScrapePlugins.RetreivalBase.ScraperBase):



	loggerPath = "Main.Manga.Mp.Cl"
	pluginName = "MangaPark Content Retreiver"
	tableKey = "mp"
	dbName = settings.DATABASE_DB_NAME
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



	def go(self):

		todo = self.retreiveTodoLinksFromDB()
		if not runStatus.run:
			return
		self.processTodoLinks(todo)



if __name__ == "__main__":
	import utilities.testBase as tb

	with tb.testSetup(startObservers=False):
		mon = ContentLoader()
		# mon.getSeriesUrls()
		# mon.getItemPages(('http://mangapark.com/manga/zai-x-10-yamauchi-yasunobu', 'Zai x 10'))
		mon.go()
