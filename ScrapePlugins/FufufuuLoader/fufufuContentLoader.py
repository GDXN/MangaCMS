import webFunctions
import re
import os
import os.path

import random
import sys

from nameTools import sanitizeString as nt_sanitizeString
from nameTools import makeFilenameSafe as nt_makeFilenameSafe

import runStatus
import time
import urllib.request, urllib.parse, urllib.error
import traceback

import bs4
import settings



import ScrapePlugins.RetreivalDbBase

class FuFuFuuContentLoader(ScrapePlugins.RetreivalDbBase.ScraperDbBase):

	loggerPath  = "Main.Fu.Cl"
	pluginName  = "Fufufu Content Retreiver"
	tableKey    = "fu"
	dbName      = settings.dbName
	dlPath      = settings.fuSettings["dlDir"]
	urlBase     = "http://fufufuu.net/"

	wg          = webFunctions.WebGetRobust()

	tableName = "HentaiItems"

	def getDirDict(self, dlPath):

		targetContents = os.listdir(dlPath)
		targetContents.sort()
		#self.log.info("targetContents", targetContents)
		targets = {}
		self.log.info("Loading Output Dirs...",)
		for item in targetContents:
			fullPath = os.path.join(dlPath, item)
			#self.log.info(item, os.path.isdir(item))
			if os.path.isdir(fullPath):
				#self.log.info(item, " is a dir", fullPath)
				targets[nt_sanitizeString(item)] = fullPath
		self.log.info("Done")

		return targets

	def go(self):


		todo = self.retreiveTodoLinksFromDB()

		if not runStatus.run:
			return
		if todo:
			self.processTodoLinks(todo)

	def retreiveTodoLinksFromDB(self):

		cur = self.conn.cursor()


		self.log.info("Fetching items from db...",)


		ret = cur.execute('SELECT sourceUrl,tags FROM AllMangaItems WHERE dlState=0 AND sourceSite=? ORDER BY retreivalTime DESC;', (self.tableKey, ))
		rets = ret.fetchall()
		if not rets:
			self.log.info("No items")
			return
		self.log.info("Done")

		items = []
		for row in rets:
			#self.log.info("Row = ", row)
			url, tags = row

			items.append([url, tags])
		self.log.info("Have %s new items to retreive in FufufuuDownloader" % len(items))
		return items


	def retag(self):
		retagTimeThresh = time.time()-settings.fuSettings["retag"]
		cur = self.conn.cursor()
		ret = cur.execute('SELECT sourceUrl,tags FROM AllMangaItems WHERE lastUpdate<? AND sourceSite=? AND dlState=2 ORDER BY retreivalTime DESC;', (retagTimeThresh, self.tableKey))

		rets = ret.fetchall()
		if not rets:
			self.log.info("No items")
			return
		self.log.info("Done")

		items = []
		for row in rets:
			#self.log.info("Row = ", row)
			url, tags = row

			items.append([url, tags])
		self.log.info("Have %s new items to retag in FufufuuDownloader" % len(items))

		for url, tags in items[:30]:

			self.downloadItem(url, tags, retagOnly=True)

			if not runStatus.run:
				return


	def processTodoLinks(self, inLinks):
		self.wg.updateCookiesFromFile()
		for linkUrl, tags in inLinks:
			self.downloadItem(linkUrl, tags)
			delay = random.randint(5, 45)
			for x in range(delay):
				time.sleep(1)
				remaining = delay-x
				sys.stdout.write("\rFuu CL sleeping %d       " % remaining)
				sys.stdout.flush()
				if not runStatus.run:
					self.log.info("Breaking due to exit flag being set")
					return


	def downloadItem(self, sourceUrl, srcTags, retagOnly=False):

		if retagOnly:
			self.log.warn("RETAGGING OLD ITEMS! No download is normal behaviour!")
		else:
			self.updateDbEntry(sourceUrl, dlState=1)

		dirDict = self.getDirDict(self.dlPath)
		#self.log.info("%s %s", dirDict, linkDict["dlLink"])
		self.log.info("Retreiving item: %s", sourceUrl)

		# with open("Freezing c145   Fufufuu.htm", "r") as fp:
		# 	cont = fp.read()

		try:

			cont = self.wg.getpage(sourceUrl)

		except urllib.error.URLError:

			if not retagOnly:
				self.updateDbEntry(sourceUrl, dlState=-1, downloadPath="ERROR", fileName="ERROR: FAILED (source page 404)")


			self.updateDbEntry(sourceUrl, lastUpdate=time.time())
			return

		if cont == None:

			if not retagOnly:
				self.updateDbEntry(sourceUrl, dlState=-1, downloadPath="ERROR", fileName="ERROR: FAILED (source page 404)")

			self.updateDbEntry(sourceUrl, lastUpdate=time.time())
			return

		soup = bs4.BeautifulSoup(cont)
		try:
			reqToken = soup.find("input", attrs={"name" : "csrfmiddlewaretoken"})
			postDict = {reqToken["name"]: reqToken["value"]}

		except:
			self.log.error("Could not retreive access token for download page.")

			if not retagOnly:
				self.updateDbEntry(sourceUrl, dlState=-1, downloadPath="TEMP UNAVAILABLE", fileName="ERROR: Page temporarily unavailable")

			self.updateDbEntry(sourceUrl, lastUpdate=time.time())
			return

		info = soup.find("table", class_="manga-info-table")

		infoDict = {}
		try:
			for item in info.find_all("tr"):
				key, val = item.find_all("td")


				# Track items in the current tag, and skip them if there are duplicates.
				# Yeah, there are lots of tags where there is `Tag` and `tag`. For some reason.
				# Wat
				itemsCheck = []
				locTags = []
				for item in val.find_all("a"):
					itemText = item.get_text().rstrip().lstrip()

					if not itemText.lower() in itemsCheck:
						locTags.append(itemText.lower().rstrip(", ").lstrip(", ").replace(" ", "-"))
						itemsCheck.append(itemText.lower())

				infoDict[key.get_text()] = locTags
			self.log.info("Infodict = %s", infoDict)
		except:
			traceback.print_exc()





		if not "Tank" in infoDict:
			tankobon = "=0= One-Shot"
		else:
			tankobon = nt_makeFilenameSafe(infoDict["Tank"].pop())


		tankKey = nt_sanitizeString(tankobon)
		if tankKey in dirDict:
			folderPath = dirDict[tankKey]
		else:
			folderPath = os.path.join(self.dlPath, tankobon)
			if not os.path.exists(folderPath):
				os.mkdir(folderPath)
			else:
				self.log.warning("Folderpath already exists?: %s", folderPath)


		self.log.info("Folderpath: %s", folderPath)
		#self.log.info(os.path.join())

		#self.log.info("infoDict = ", infoDict)
		#self.log.info("postDict = ", postDict)

		try:
			fragment = soup.find("span", attrs={"class" : "icon-down-circled"})
			fragment = fragment.find_parent("form")["action"]

		except:
			self.log.error("Could not retreive download link URL.")

			if not retagOnly:
				self.updateDbEntry(sourceUrl, dlState=-1, downloadPath="TEMP UNAVAILABLE", fileName="ERROR: Page temporarily unavailable")


			self.updateDbEntry(sourceUrl, lastUpdate=time.time())
			return


		tagsTemp = []
		if infoDict:

			for key in infoDict.keys():
				for value in infoDict[key]:

					if not "content" in key.lower():
						tagsTemp.append("-".join((key, value)))
					else:
						tagsTemp.append(value)


		srcTags = srcTags.split(" ")
		allTags = set(tagsTemp) | set(srcTags)


		tags = " ".join(allTags).replace("  ", " ")  # replace() is probably pointless

		self.log.info("Len srcTags = %s, Len newTags = %s, Len totalTags = %s.", len(srcTags), len(tagsTemp), len(allTags))
		# print ("Original tags = ")
		# for tag in srcTags:
		# 	print("		tag: ", tag)
		# print ("New tags = ")
		# for tag in tagsTemp:
		# 	print("		tag: ", tag)


		self.updateDbEntry(sourceUrl, seriesName=tankobon, tags=tags, lastUpdate=time.time())


		if retagOnly:  # We're just updating the tags, not actually downloading the file


			return

		contentUrl = urllib.parse.urljoin(self.urlBase, fragment)
		# self.log.info(contentUrl)

		try:
			content, handle = self.wg.getpage(contentUrl, returnMultiple=True, addlHeaders={'Referer': sourceUrl}, postData=postDict)
		except urllib.error.URLError:
			self.updateDbEntry(sourceUrl, dlState=-1, downloadPath="ERROR", fileName="ERROR: FAILED (Archive page 404)")
			return
		# self.log.info(len(content))

		if handle:
			# self.log.info("handle = ", handle)
			# self.log.info("geturl", handle.geturl())
			fileN = urllib.parse.unquote(urllib.parse.urlparse(handle.geturl())[2].split("/")[-1])
			fileN = bs4.UnicodeDammit(fileN).unicode_markup
			# print("Filename = ", fileN)



			# print("Tags = ", tagsTemp)

			fullFileName = fileN
			if not (fullFileName.lower().endswith(".zip") or fullFileName.lower().endswith(".rar")):
				print(fullFileName.lower().endswith(".zip"), fullFileName.lower().endswith(".rar"))
				self.log.error("Filename does not end with a zip/rar extension!")
				self.log.error("Filename = \"%s\"", fullFileName)
				return

			fileN = nt_makeFilenameSafe(fullFileName)


			# self.log.info("geturl with processing", fileN)
			wholePath = os.path.join(folderPath, fileN)
			try:
				with open(wholePath, "wb") as fp:
					fp.write(content)

					self.log.info("Successfully Saved to path: %s", wholePath)
					self.updateDbEntry(sourceUrl, dlState=2, downloadPath=folderPath, fileName=fileN)

			# if we have a text-page rather then a binary string containing the file.
			except TypeError:
					self.log.error("Download failed!: %s", wholePath)
					self.updateDbEntry(sourceUrl, dlState=-1, downloadPath=folderPath, fileName=fileN)


		else:

			self.updateDbEntry(sourceUrl, dlState=-1, downloadPath="ERROR", fileName="ERROR: FAILED")

