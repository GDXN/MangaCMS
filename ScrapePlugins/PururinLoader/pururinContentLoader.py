
# -*- coding: utf-8 -*-

import runStatus
runStatus.preloadDicts = False
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

import processDownload

import ScrapePlugins.RetreivalDbBase

class PururinContentLoader(ScrapePlugins.RetreivalDbBase.ScraperDbBase):




	dbName = settings.DATABASE_DB_NAME
	loggerPath = "Main.Manga.Pururin.Cl"
	pluginName = "Pururin Content Retreiver"
	tableKey   = "pu"
	urlBase = "http://pururin.com"

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	tableName = "HentaiItems"

	def checkLogin(self):
		acctPage = self.wg.getpage("http://pururin.com/account/home")
		if "You don't have an account!" in acctPage:
			return False
		else:
			return True

	def login(self):
		loginPage = self.wg.getpage("http://pururin.com/account/recover",
				addlHeaders={'Referer': 'http://pururin.com/account/recover'},
				postData={'token': settings.puSettings["accountKey"], "recover-token": "Submit"} )

		if "Success! Welcome back" in loginPage:
			return True

		else:
			return False

	def loginIfNeeded(self):
		self.log.info("Checking login state on Pururin")
		if not self.checkLogin():
			if not self.login():
				self.log.error("Could not log in. Is your account key set?")
		self.log.info("Logged in!")


	def go(self):

		self.wg.stepThroughCloudFlare("http://pururin.com/", titleContains="Pururin")
		self.loginIfNeeded()
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
			items.append(row)
		self.log.info("Have %s new items to retreive in PururinDownloader" % len(items))

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
				sys.stdout.write("\rPururin CL sleeping %d          " % remaining)
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


		cont = self.wg.getpage(sourcePage, addlHeaders={'Referer': 'http://pururin.com/'})
		soup = bs4.BeautifulSoup(cont, "lxml")

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

			soup = bs4.BeautifulSoup(gatewayPage, "lxml")
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
			try:
				arch = zipfile.ZipFile(wholePath, "w")
			except OSError:
				title = title.encode('ascii','ignore').decode('ascii')
				fileN = title+".zip"
				fileN = nt.makeFilenameSafe(fileN)
				wholePath = os.path.join(linkDict["dirPath"], fileN)
				arch = zipfile.ZipFile(wholePath, "w")

			for imageName, imageContent in images:
				arch.writestr(imageName, imageContent)
			arch.close()


			self.log.info("Successfully Saved to path: %s", wholePath)


			self.updateDbEntry(linkDict["sourceUrl"], downloadPath=linkDict["dirPath"], fileName=fileN)

			# Deduper uses the path info for relinking, so we have to dedup the item after updating the downloadPath and fileN
			dedupState = processDownload.processDownload(None, wholePath, pron=True, deleteDups=True, includePHash=True)
			self.log.info( "Done")

			if dedupState:
				self.addTags(sourceUrl=linkDict["sourceUrl"], tags=dedupState)


			self.updateDbEntry(linkDict["sourceUrl"], dlState=2)
			self.conn.commit()


			return wholePath

		else:

			self.updateDbEntry(linkDict["sourceUrl"], dlState=-1, downloadPath="ERROR", fileName="ERROR: FAILED")

			self.conn.commit()
			return False

if __name__ == "__main__":
	import utilities.testBase as tb

	with tb.testSetup(startObservers=False):

		run = PururinContentLoader()
		run.go()

