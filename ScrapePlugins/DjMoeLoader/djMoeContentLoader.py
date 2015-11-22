
# -*- coding: utf-8 -*-

import webFunctions
import os
import os.path

import random
import sys

import nameTools as nt

import runStatus
import time
import urllib.request, urllib.parse, urllib.error
import traceback

import settings
import bs4
import logging

import processDownload
from ScrapePlugins.DjMoeLoader import tagsLUT

import ScrapePlugins.RetreivalDbBase

class DjMoeContentLoader(ScrapePlugins.RetreivalDbBase.ScraperDbBase):
	log = logging.getLogger("Main.Manga.DjM.Cl")


	dbName = settings.DATABASE_DB_NAME
	loggerPath = "Main.Manga.DjM.Cl"
	pluginName = "DjMoe Content Retreiver"
	tableKey   = "djm"
	urlBase = "http://www.doujin-moe.us/"

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")
	tableName = "HentaiItems"

	shouldCanonize = False
	def retag(self):
		retagUntaggedThresh = time.time()-settings.djSettings["retagMissing"]
		retagThresh = time.time()-settings.djSettings["retag"]
		with self.conn.cursor() as cur:

			ret = cur.execute("SELECT sourceUrl,tags FROM {tableName} WHERE lastUpdate<%s AND sourceSite=%s AND dlState=2 AND (tags IS NULL OR tags='') ORDER BY retreivalTime DESC;".format(tableName=self.tableName), (retagUntaggedThresh, self.tableKey))
			rets = cur.fetchall()
			if not rets:
				ret = cur.execute("SELECT sourceUrl,tags FROM {tableName} WHERE lastUpdate<%s AND sourceSite=%s AND dlState=2 AND (tags IS NULL OR tags='') ORDER BY retreivalTime DESC;".format(tableName=self.tableName), (retagThresh, self.tableKey))
				rets = cur.fetchall()
				if not rets:
					self.log.info("Done")
					return

		items = []
		for row in rets:
			#self.log.info("Row = ", row)
			contentId = row[0]

			items.append(contentId)
		self.log.info("Have %s new items to retag in Doujin Moe Retagger" % len(items))

		for contentId in items:
			# print("contentId = ", contentId)
			if not "import" in contentId:
				conf = {"sourceUrl" : contentId}
				ret = self.getDownloadUrl(conf, retag=True)
				# print(ret)




			if not runStatus.run:
				return


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

			items.append(row)  # Actually the contentID
		self.log.info("Have %s new items to retreive in DjMDownloader" % len(items))

		return items


	def processTodoLinks(self, inLinks):

		for contentId in inLinks:
			print("Loopin!")
			try:
				url = self.getDownloadUrl(contentId)
				if url:
					self.doDownload(url)
					delay = random.randint(5, 30)
				else:
					return
			except:
				print("ERROR WAT?")
				traceback.print_exc()
				delay = 1


			for x in range(delay):
				time.sleep(1)
				remaining = delay-x
				sys.stdout.write("\rDjM CL sleeping %d          " % remaining)
				sys.stdout.flush()
				if not runStatus.run:
					self.log.info("Breaking due to exit flag being set")
					return


	def getDirAndFName(self, soup):
		title = soup.find("div", class_="title")
		if not title:
			raise ValueError("Could not find title. Wat?")
		titleSplit = title.get_text().split("»")
		safePath = [nt.makeFilenameSafe(item.rstrip().lstrip()) for item in titleSplit]
		fqPath = os.path.join(settings.djSettings["dlDir"], *safePath)
		dirPath, fName = fqPath.rsplit("/", 1)
		self.log.debug("dirPath = %s", dirPath)
		self.log.debug("fName = %s", fName)
		return dirPath, fName, title.get_text()

	def getDownloadUrl(self, linkDict, retag=False):
		self.log.info("Retreiving item: %s", linkDict["sourceUrl"])

		if retag:
			self.log.warning("Retagging. No download is expected behaviour.")
		else:
			self.updateDbEntry(linkDict["sourceUrl"], dlState=1)
			self.conn.commit()

		#self.log.info("%s %s", dirDict, linkDict["sourceUrl"])
		sourcePage = urllib.parse.urljoin(self.urlBase, linkDict["sourceUrl"])

		linkDict["contentId"] = linkDict["sourceUrl"]
		linkDict["sourceUrl"] = sourcePage

		cont = self.wg.getpage(sourcePage)

		soup = bs4.BeautifulSoup(cont)
		if not soup:
			self.log.critical("No download at url %s! SourceUrl = %s", sourcePage, linkDict["sourceUrl"])
			if not retag:
				self.updateDbEntry(linkDict["sourceUrl"], dlState=-1)
				self.conn.commit()
			raise IOError("Invalid webpage")


		try:
			linkDict["dirPath"], linkDict["originName"], linkDict["seriesName"] = self.getDirAndFName(soup)
		except AttributeError:
			self.log.critical("No download at url %s! SourceUrl = %s", sourcePage, linkDict["sourceUrl"])
			if retag:
				# page is gone. Skip it and set it to ignore in the future
				self.updateDbEntry(linkDict["contentId"], lastUpdate=time.time())
				return

			self.updateDbEntry(linkDict["sourceUrl"], dlState=-1)
			self.conn.commit()
			return

		except ValueError:
			self.log.critical("No download at url %s! SourceUrl = %s", sourcePage, linkDict["sourceUrl"])
			if retag:
				# page is gone. Skip it and set it to ignore in the future
				self.updateDbEntry(linkDict["contentId"], lastUpdate=time.time())
				return

			self.updateDbEntry(linkDict["sourceUrl"], dlState=-1)
			self.conn.commit()
			return



		note = soup.find("div", class_="message")
		if note == None or note.string == None:
			linkDict["note"] = " "
		else:
			linkDict["note"] = nt.makeFilenameSafe(note.string)

		tags = soup.find("div", class_="tag_list")
		if tags:
			tagList = []
			for tag in tags.find_all("a"):
				tagStr = tag.get_text()
				if tagStr in tagsLUT.tagLutDict:
					tagStr = tagsLUT.tagLutDict[tagStr]
				tagList.append(tagStr.lower().rstrip(", ").lstrip(", ").replace(" ", "-"))
		else:
			tagList = []

		tagStr = ' '.join(tagList)

		for skipTag in settings.skipTags:
			if skipTag in tagStr:
				self.log.info("Skipped tag '%s' in tags '%s'. Do not want.", skipTag, tagStr)
				return None

		linkDict["tags"] = tagStr

		if not os.path.exists(linkDict["dirPath"]):
			os.makedirs(linkDict["dirPath"])
		else:
			self.log.info("Folder Path already exists?: %s", linkDict["dirPath"])


		self.log.info("Folderpath: %s", linkDict["dirPath"])
		#self.log.info(os.path.join())

		self.log.debug("Linkdict = ")
		for key, value in list(linkDict.items()):
			self.log.debug("		%s - %s", key, value)


		if "tags" in linkDict and "note" in linkDict:
			self.updateDbEntry(linkDict["contentId"], tags=linkDict["tags"], note=linkDict["note"], lastUpdate=time.time())
			self.conn.commit()

		return linkDict

	def doDownload(self, linkDict):

		contentUrl = urllib.parse.urljoin(self.urlBase, "/zip.php?token=%s" % linkDict["contentId"])
		content, handle = self.wg.getpage(contentUrl, returnMultiple=True, addlHeaders={'Referer': linkDict["sourceUrl"]})

		# self.log.info(len(content))

		if handle:
			# self.log.info("handle = ", handle)
			# self.log.info("geturl", handle.geturl())
			urlFileN = urllib.parse.unquote(urllib.parse.urlparse(handle.geturl())[2].split("/")[-1])
			urlFileN = bs4.UnicodeDammit(urlFileN).unicode_markup
			urlFileN.encode("utf-8")




			# DjMoe is apparently returning "zip.php" for ALL filenames.
			# Blargh
			if urlFileN == "zip.php":
				urlFileN = ".zip"
				fileN = "%s%s" % (linkDict["originName"], urlFileN)
			else:
				self.log.error("Unknown file extension?")
				self.log.error("Unknown file extension?")
				self.log.error("Dict filename = %s", linkDict["originName"])
				self.log.error("URL filename = %s", urlFileN)
				fileN = "%s - %s" % (linkDict["originName"], urlFileN)

			fileN = nt.makeFilenameSafe(fileN)


			# self.log.info("geturl with processing", fileN)
			wholePath = os.path.join(linkDict["dirPath"], fileN)
			self.log.info("Complete filepath: %s", wholePath)

			fp = open(wholePath, "wb")
			fp.write(content)
			fp.close()
			self.log.info("Successfully Saved to path: %s", wholePath)


			self.updateDbEntry(linkDict["contentId"], downloadPath=linkDict["dirPath"], fileName=fileN)

			# Deduper uses the path info for relinking, so we have to dedup the item after updating the downloadPath and fileN
			dedupState = processDownload.processDownload(None, wholePath, pron=True, deleteDups=True)
			self.log.info( "Done")

			if dedupState:
				self.addTags(sourceUrl=linkDict["contentId"], tags=dedupState)

			self.updateDbEntry(linkDict["contentId"], dlState=2)
			self.conn.commit()





		else:

			self.updateDbEntry(linkDict["contentId"], dlState=-1, downloadPath="ERROR", fileName="ERROR: FAILED")

			# cur.execute('UPDATE djmoe SET downloaded=1 WHERE contentID=?;', (linkDict["contentId"], ))
			# cur.execute('UPDATE djmoe SET dlPath=?, dlName=?, itemTags=?  WHERE contentID=?;', ("ERROR", 'ERROR: FAILED', "N/A", linkDict["contentId"]))
			# self.log.info("fetchall = ", cur.fetchall())
			self.conn.commit()



if __name__ == "__main__":
	import utilities.testBase as tb

	with tb.testSetup(startObservers=False):

		# run = HBrowseRetagger()
		run = DjMoeContentLoader()

		run.resetStuckItems()
		run.go()
