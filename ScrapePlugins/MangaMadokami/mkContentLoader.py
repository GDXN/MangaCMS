
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
	("manga.madokami.com", settings.mkSettings["login"], settings.mkSettings["passWd"]),
	("http://manga.madokami.com", settings.mkSettings["login"], settings.mkSettings["passWd"]),
	("https://manga.madokami.com", settings.mkSettings["login"], settings.mkSettings["passWd"]),
	]


class MkContentLoader(ScrapePlugins.RetreivalDbBase.ScraperDbBase):


	wg = webFunctions.WebGetRobust(creds=HTTPS_CREDS)
	loggerPath = "Main.Manga.Mk.Cl"
	pluginName = "Manga.Madokami Content Retreiver"
	tableKey = "mk"
	dbName = settings.DATABASE_DB_NAME

	retreivalThreads = 1

	tableName = "MangaItems"
	urlBase = "https://manga.madokami.com/"

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
		pgctnt, pghandle = self.wg.getpage(fileUrl, returnMultiple = True, addlHeaders={'Referer': "https://manga.madokami.com"})
		pageUrl = pghandle.geturl()
		hName = urllib.parse.urlparse(pageUrl)[2].split("/")[-1]
		self.log.info( "HName: %s", hName, )
		self.log.info( "Size = %s", len(pgctnt))


		return pgctnt, hName


	def getLink(self, link):


		seriesName = link["seriesName"]
		seriesName = seriesName.replace("[", "(").replace("]", "(")
		safeBaseName = nt.makeFilenameSafe(link["seriesName"])



		if seriesName in nt.dirNameProxy:
			self.log.info( "Have target dir for '%s' Dir = '%s'", seriesName, nt.dirNameProxy[seriesName]['fqPath'])
			link["targetDir"] = nt.dirNameProxy[seriesName]["fqPath"]
		else:
			self.log.info( "Don't have target dir for: %s Using default for: %s, full name = %s", seriesName, link["seriesName"], link["originName"])
			targetDir = os.path.join(settings.jzSettings["dirs"]['mDlDir'], safeBaseName)
			if not os.path.exists(targetDir):
				try:
					os.makedirs(targetDir)
					link["targetDir"] = targetDir
					self.updateDbEntry(link["sourceUrl"],flags=" ".join([link["flags"], "newdir"]))
					self.conn.commit()

					self.conn.commit()
				except OSError:
					self.log.critical("Directory creation failed?")
					self.log.critical(traceback.format_exc())
			else:
				self.log.warning("Directory not found in dir-dict, but it exists!")
				self.log.warning("Directory-Path: %s", targetDir)
				link["targetDir"] = targetDir

				self.updateDbEntry(link["sourceUrl"],flags=" ".join([link["flags"], "haddir"]))
				self.conn.commit()




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
		imageExts = ["jpg", "png", "bmp"]
		if not any([ext.endswith(ex) for ex in imageExts]):
			dedupState = processDownload.processDownload(False, fqFName, deleteDups=True)
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




class Runner(ScrapePlugins.RunBase.ScraperBase):
	loggerPath = "Main.Manga.MkC.Run"

	pluginName = "MkCLoader"

	def _go(self):
		self.log.info("Checking Mk feeds for updates")
		fl = MkContentLoader()
		fl.go()
		fl.closeDB()


if __name__ == "__main__":
	import utilities.testBase as tb

	with tb.testSetup(startObservers=True):

		run = Runner()
		run.go()


