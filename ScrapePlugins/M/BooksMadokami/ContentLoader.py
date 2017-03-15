
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
import ScrapePlugins.RunBase

from concurrent.futures import ThreadPoolExecutor

import processDownload


HTTPS_CREDS = [
	("manga.madokami.al", settings.mkSettings["login"], settings.mkSettings["passWd"]),
	("http://manga.madokami.al", settings.mkSettings["login"], settings.mkSettings["passWd"]),
	("https://manga.madokami.al", settings.mkSettings["login"], settings.mkSettings["passWd"]),
	]


class ContentLoader(ScrapePlugins.RetreivalDbBase.ScraperDbBase):


	wg = webFunctions.WebGetRobust(creds=HTTPS_CREDS)
	loggerPath = "Main.Books.Mk.Cl"
	pluginName = "Books.Madokami Content Retreiver"
	tableKey = "mk"
	dbName = settings.DATABASE_DB_NAME

	retreivalThreads = 1

	tableName = "BookItems"
	urlBase = "https://manga.madokami.al/"

	def retreiveTodoLinksFromDB(self):

		self.log.info( "Fetching items from db...",)

		rows = self.getRowsByValue(dlState=0)

		self.log.info( "Done")
		if not rows:
			self.log.info("No new items, nothing to do.")
			return


		items = []
		for item in rows:
			# print("Item", item)
			item["retreivalTime"] = time.gmtime(item["retreivalTime"])

			items.append(item)

		self.log.info( "Have %s new items to retreive in MkDownloader" % len(items))


		items = sorted(items, key=lambda k: k["retreivalTime"], reverse=True)

		return items[:500]




	def getLinkFile(self, fileUrl):

		scheme, netloc, path, params, query, fragment = urllib.parse.urlparse(fileUrl)
		path = urllib.parse.quote(path)
		fileUrl = urllib.parse.urlunparse((scheme, netloc, path, params, query, fragment))

		pgctnt, pghandle = self.wg.getpage(fileUrl, returnMultiple = True, addlHeaders={'Referer': "https://manga.madokami.al"})
		pageUrl = pghandle.geturl()
		hName = urllib.parse.urlparse(pageUrl)[2].split("/")[-1]
		self.log.info( "HName: %s", hName, )
		self.log.info( "Size = %s", len(pgctnt))


		return pgctnt, hName


	def getLink(self, link):


		seriesName = link["seriesName"]
		seriesName = seriesName.replace("[", "(").replace("]", "(")
		safeBaseName = nt.makeFilenameSafe(link["seriesName"])


		targetDir = os.path.join(settings.mkSettings["dirs"]['bookDir'], safeBaseName)
		if not os.path.exists(targetDir):
			try:
				self.log.info( "Need to create directory for: %s Using default for: %s, full name = %s", seriesName, link["seriesName"], link["originName"])
				os.makedirs(targetDir)
				link["targetDir"] = targetDir
				self.updateDbEntry(link["sourceUrl"],flags=" ".join([link["flags"], "newdir"]))

			except OSError:
				self.log.critical("Directory creation failed?")
				self.log.critical(traceback.format_exc())
		else:
			self.log.info("Have existing directory for item %s - : %s", seriesName, targetDir)
			link["targetDir"] = targetDir

			self.updateDbEntry(link["sourceUrl"],flags=" ".join([link["flags"], "haddir"]))




		sourceUrl, originFileName = link["sourceUrl"], link["originName"]

		self.log.info( "Should retreive: %s, url - %s", originFileName, sourceUrl)

		self.updateDbEntry(sourceUrl, dlState=1)


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

		fName = "%s" % originFileName
		fName = nt.makeFilenameSafe(fName)

		fqFName = os.path.join(link["targetDir"], fName)
		self.log.info( "SaveName = %s", fqFName)


		loop = 1
		while os.path.exists(fqFName):
			root, ext = os.path.splitext(fqFName)
			fName = "%s - (%d) - %s" % (root, loop,  ext)
			fqFName = os.path.join(link["targetDir"], fName)
			loop += 1
		self.log.info( "Writing file")

		filePath, fileName = os.path.split(fqFName)

		try:
			chop = len(fileName)-4

			wholePath = "ERROR"
			while 1:

				try:
					fileName = fileName[:chop]+fileName[-4:]
					# self.log.info("geturl with processing", fileName)
					wholePath = os.path.join(filePath, fileName)
					self.log.info("Complete filepath: %s", wholePath)

					#Write all downloaded files to the archive.
					with open(wholePath, "wb") as fp:
						fp.write(content)
					self.log.info("Successfully Saved to path: %s", wholePath)
					break
				except IOError:
					chop = chop - 1
					if chop < 200:
						raise RuntimeError("Don't know what's going on, but a file truncated too far!")
					self.log.warn("Truncating file length to %s characters.", chop)




		except TypeError:
			self.log.error("Failure trying to retreive content from source %s", sourceUrl)
			self.updateDbEntry(sourceUrl, dlState=-4, downloadPath=filePath, fileName=fileName)
			return
		#self.log.info( filePath)

		ext = os.path.splitext(fileName)[-1]
		dedupState = ""

		self.log.info( "Done")
		self.updateDbEntry(sourceUrl, dlState=2, downloadPath=filePath, fileName=fileName, tags=dedupState)
		return





class Runner(ScrapePlugins.RunBase.ScraperBase):
	loggerPath = "Main.Manga.MkC.Run"

	pluginName = "MkCLoader"

	def _go(self):
		self.log.info("Checking Mk feeds for updates")
		fl = ContentLoader()
		fl.go()
		fl.closeDB()


if __name__ == "__main__":
	import utilities.testBase as tb

	with tb.testSetup():

		run = Runner()
		run.go()


