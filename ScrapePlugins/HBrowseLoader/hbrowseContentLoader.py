
# -*- coding: utf-8 -*-

import webFunctions
import os
import os.path

import random
import sys
import zipfile
import nameTools as nt

import runStatus
import time
import urllib.request, urllib.parse, urllib.error
import traceback

import settings
import bs4

import archCleaner

import ScrapePlugins.RetreivalDbBase

class HBrowseContentLoader(ScrapePlugins.RetreivalDbBase.ScraperDbBase):

	archCleaner = archCleaner.ArchCleaner()


	dbName = settings.dbName
	loggerPath = "Main.HBrowse.Cl"
	pluginName = "H-Browse Content Retreiver"
	tableKey   = "hb"
	urlBase = "http://www.hbrowse.com/"

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	tableName = "HentaiItems"

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

			# Wait 36 hours after an item is uploaded to actually scrape it, since it looks like uploads
			# are almost always in a fucked up order at the start
			# Seriously, these kind of things are sequentially numbered. How can you fuck that up?
			# They manage, somehow.
			if row["retreivalTime"] < (time.time() + 60*60*36):
				items.append(row)  # Actually the contentID
		self.log.info("Have %s new items to retreive in HBrowseDownloader" % len(items))

		return items


	def processTodoLinks(self, inLinks):

		for contentId in inLinks:
			print("Loopin!")
			try:
				url = self.getDownloadInfo(contentId)
				self.doDownload(url)


				delay = random.randint(5, 30)
			except:
				print("ERROR WAT?")
				traceback.print_exc()
				delay = 1


			for x in range(delay):
				time.sleep(1)
				remaining = delay-x
				sys.stdout.write("\rhbrowse CL sleeping %d          " % remaining)
				sys.stdout.flush()
				if not runStatus.run:
					self.log.info("Breaking due to exit flag being set")
					return


	def getFileName(self, soup):
		title = soup.find("h1", class_="otitle")
		if not title:
			raise ValueError("Could not find title. Wat?")
		return title.get_text()

	def getCategoryTags(self, soup):
		tagTable = soup.find("table", class_="table-info")

		tags = []

		formatters = {
						"Artist"     : "Artist",
						"Circle"     : "Circles",
						"Parody"     : "Parody",
						"Characters" : "Characters",
						"Contents"   : "",
						"Language"   : "",
						"Scanlator"  : "scanlators",
						"Convention" : "Convention"
					}

		ignoreTags = [
					"Uploader",
					"Pages",
					"Ranking",
					"Rating"]

		category = "Unknown?"
		for tr in tagTable.find_all("tr"):
			if len(tr.find_all("td")) != 2:
				continue

			what, values = tr.find_all("td")

			what = what.get_text()
			if what in ignoreTags:
				continue
			elif what == "Category":
				category = values.get_text().strip()
				if category == "Manga One-shot":
					category = "=0= One-Shot"
			elif what in formatters:
				for li in values.find_all("li"):
					tag = " ".join([formatters[what], li.get_text()])
					tag = tag.strip()
					tag = tag.replace("  ", " ")
					tag = tag.replace(" ", "-")
					tags.append(tag)

		return category, tags

	def getNote(self, soup):
		note = soup.find("div", class_="gallery-description")
		if note == None:
			note = " "
		else:
			note = note.get_text()

	def getDownloadInfo(self, linkDict, retag=False):
		sourcePage = linkDict["sourceUrl"]

		self.log.info("Retreiving item: %s", sourcePage)

		if not retag:
			self.updateDbEntry(linkDict["sourceUrl"], dlState=1)


		cont = self.wg.getpage(sourcePage, addlHeaders={'Referer': 'http://hbrowse.com/'})
		soup = bs4.BeautifulSoup(cont)

		if not soup:
			self.log.critical("No download at url %s! SourceUrl = %s", sourcePage, linkDict["sourceUrl"])
			raise IOError("Invalid webpage")

		category, tags = self.getCategoryTags(soup)
		note = self.getNote(soup)
		tags = ' '.join(tags)

		linkDict['dirPath'] = os.path.join(settings.puSettings["dlDir"], nt.makeFilenameSafe(category))

		if not os.path.exists(linkDict["dirPath"]):
			os.makedirs(linkDict["dirPath"])
		else:
			self.log.info("Folder Path already exists?: %s", linkDict["dirPath"])


		self.log.info("Folderpath: %s", linkDict["dirPath"])
		#self.log.info(os.path.join())

		dlPage = soup.find("a", class_="link-next")
		linkDict["dlLink"] = urllib.parse.urljoin(self.urlBase, dlPage["href"])

		self.log.debug("Linkdict = ")
		for key, value in list(linkDict.items()):
			self.log.debug("		%s - %s", key, value)


		if tags:
			self.log.info("Adding tag info %s", tags)

			self.addTags(sourceUrl=linkDict["sourceUrl"], tags=tags)
		if note:
			self.log.info("Adding note %s", note)
			self.updateDbEntry(linkDict["sourceUrl"], note=note)


		self.updateDbEntry(linkDict["sourceUrl"], seriesName=category, lastUpdate=time.time())



		return linkDict


	def doDownload(self, linkDict):


		images = []
		title = None
		nextPage = linkDict["dlLink"]

		while nextPage:
			gatewayPage = self.wg.getpage(nextPage, addlHeaders={'Referer': linkDict["sourceUrl"]})

			soup = bs4.BeautifulSoup(gatewayPage)
			titleCont = soup.find("div", class_="image-menu")

			title = titleCont.h1.get_text()
			title = title.replace("Reading ", "")
			title, dummy = title.rsplit(" Page ", 1)
			title = title.strip()


			imageUrl = soup.find("img", class_="b")
			imageUrl = urllib.parse.urljoin(self.urlBase, imageUrl["src"])

			imagePath = urllib.parse.urlsplit(imageUrl)[2]
			imageFileName = imagePath.split("/")[-1]


			imageData = self.wg.getpage(imageUrl, addlHeaders={'Referer': nextPage})

			images.append((imageFileName, imageData))
			# Find next page
			nextPageLink = soup.find("a", class_="link-next")
			if not nextPageLink:
				nextPage = None
			elif nextPageLink["href"].startswith("/finish/"):    # Break on the last image.
				nextPage = None
			else:
				nextPage = urllib.parse.urljoin(self.urlBase, nextPageLink["href"])


		# self.log.info(len(content))

		if images and title:
			fileN = title+".zip"
			fileN = nt.makeFilenameSafe(fileN)


			# self.log.info("geturl with processing", fileN)
			wholePath = os.path.join(linkDict["dirPath"], fileN)
			self.log.info("Complete filepath: %s", wholePath)

					#Write all downloaded files to the archive.
			arch = zipfile.ZipFile(wholePath, "w")
			for imageName, imageContent in images:
				arch.writestr(imageName, imageContent)
			arch.close()


			self.log.info("Successfully Saved to path: %s", wholePath)

			if not linkDict["tags"]:
				linkDict["tags"] = ""


			dedupState = self.archCleaner.processNewArchive(wholePath, deleteDups=True, includePHash=True)
			self.log.info( "Done")


			if dedupState:
				self.addTags(sourceUrl=linkDict["sourceUrl"], tags=dedupState)

			self.updateDbEntry(linkDict["sourceUrl"], dlState=2, downloadPath=linkDict["dirPath"], fileName=fileN, seriesName=linkDict["seriesName"])

			self.conn.commit()
			return wholePath

		else:

			self.updateDbEntry(linkDict["sourceUrl"], dlState=-1, downloadPath="ERROR", fileName="ERROR: FAILED")

			self.conn.commit()
			return False
