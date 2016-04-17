
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

import processDownload

import ScrapePlugins.RetreivalBase

class HBrowseContentLoader(ScrapePlugins.RetreivalBase.ScraperBase):




	dbName = settings.DATABASE_DB_NAME
	loggerPath = "Main.Manga.HBrowse.Cl"
	pluginName = "H-Browse Content Retreiver"
	tableKey   = "hb"
	urlBase = "http://www.hbrowse.com/"

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	tableName = "HentaiItems"

	retreivalThreads = 4

	shouldCanonize = False

	def getFileName(self, soup):
		title = soup.find("h1", class_="otitle")
		if not title:
			raise ValueError("Could not find title. Wat?")
		return title.get_text()

	def getCategoryTags(self, soup):
		tables = soup.find_all("table", class_="listTable")

		tags = []


		formatters = {

						'Genre'        : 'Genre',
						'Type'         : '',
						'Setting'      : '',
						'Fetish'       : 'Fetish',
						'Role'         : '',
						'Relationship' : '',
						'Male Body'    : 'Male',
						'Female Body'  : 'Female',
						'Grouping'     : 'Grouping',
						'Scene'        : '',
						'Position'     : 'Position',
						'Artist'       : "Artist"

					}

		ignoreTags = [
						'Length'
					]



		# 'Origin'       : '',  (Category)
		category = "Unknown?"
		title = "None?"
		for table in tables:
			for tr in table.find_all("tr"):
				if len(tr.find_all("td")) != 2:
					continue

				what, values = tr.find_all("td")
				what = what.get_text().strip()

				# print("Row what", what, "values", values.get_text().strip())

				if what in ignoreTags:
					continue

				elif what == "Origin":
					category = values.get_text().strip()

				elif what == "Title":
					title = values.get_text().strip()

					# If cloudflare is fucking shit up, just try to get the title from the title tag.
					if r"[email\xa0protected]" in title or r'[email protected]' in title:
						title = soup.title.get_text().split(" by ")[0]


				elif what in formatters:
					for rawTag in values.find_all("a"):
						tag = " ".join([formatters[what], rawTag.get_text().strip()])
						tag = tag.strip()
						tag = tag.replace("  ", " ")
						tag = tag.replace(" ", "-")
						tags.append(tag)

		# print("title", title)
		# print("Category", category)
		# print("Tags", tags)
		return title, category, tags

	def getGalleryStartPages(self, soup):
		linkTds = soup.find_all("td", class_="listMiddle")

		ret = []

		for td in linkTds:
			ret.append(td.a['href'])

		return ret

	def getDownloadInfo(self, linkDict, retag=False):
		sourcePage = linkDict["sourceUrl"]

		self.log.info("Retreiving item: %s", sourcePage)

		if not retag:
			self.updateDbEntry(linkDict["sourceUrl"], dlState=1)


		try:
			soup = self.wg.getSoup(sourcePage, addlHeaders={'Referer': 'http://hbrowse.com/'})
		except:
			self.log.critical("No download at url %s! SourceUrl = %s", sourcePage, linkDict["sourceUrl"])
			raise IOError("Invalid webpage")

		title, category, tags = self.getCategoryTags(soup)
		tags = ' '.join(tags)

		self.updateDbEntry(linkDict["sourceUrl"], seriesName=category, originName=title, lastUpdate=time.time())

		# Push the fixed title back into the linkdict so it's changes will be used later
		# when saving the file.
		linkDict['originName'] = title
		if tags:
			self.log.info("Adding tag info %s", tags)
			self.addTags(sourceUrl=linkDict["sourceUrl"], tags=tags)

		if retag:
			return

		linkDict['dirPath'] = os.path.join(settings.hbSettings["dlDir"], nt.makeFilenameSafe(category))

		if not os.path.exists(linkDict["dirPath"]):
			os.makedirs(linkDict["dirPath"])
		else:
			self.log.info("Folder Path already exists?: %s", linkDict["dirPath"])


		self.log.info("Folderpath: %s", linkDict["dirPath"])
		#self.log.info(os.path.join())


		startPages = self.getGalleryStartPages(soup)


		linkDict["dlLink"] = startPages



		self.log.debug("Linkdict = ")
		for key, value in list(linkDict.items()):
			self.log.debug("		%s - %s", key, value)


		return linkDict


	def fetchImages(self, linkDict):
		toFetch = {key:0 for key in linkDict["dlLink"]}
		baseUrls = [item for item in linkDict["dlLink"]]
		images = {}
		while not all(toFetch.values()):

			# get a random dict element where downloadstate = 0
			thisPage = list(toFetch.keys())[list(toFetch.values()).index(0)]

			soup = self.wg.getSoup(thisPage, addlHeaders={'Referer': linkDict["sourceUrl"]})

			imageTd = soup.find('td', class_='pageImage')

			imageUrl = urllib.parse.urljoin(self.urlBase, imageTd.img["src"])

			imagePath = urllib.parse.urlsplit(imageUrl)[2]
			chapter = imageUrl.split("/")[-2]
			imName = imagePath.split("/")[-1]
			imageFileName = '{c} - {i}'.format(c=chapter, i=imName)

			self.log.info("Using filename '%s'", imageFileName)


			imageData = self.wg.getpage(imageUrl, addlHeaders={'Referer': thisPage})
			images[imageFileName] = imageData

			toFetch[thisPage] = 1
			# Find next page

			nextPageLink = imageTd.a['href']

			# Block any cases where the next page url is higher then
			# the baseURLs, so that we don't fetch links back up the
			# hierarchy.
			if nextPageLink != linkDict["sourceUrl"] and not any([nextPageLink in item for item in baseUrls]):

				if not nextPageLink in toFetch:
					toFetch[nextPageLink] = 0

		# Use a dict, and then flatten to a list because we will fetch some items twice.
		# Basically, `http://www.hbrowse.com/{sommat}/c00000` has the same image
		# as  `http://www.hbrowse.com/{sommat}/c00000/00001`, but the strings are not matches.
		images = [(key, value) for key, value in images.items()]
		return images


	def doDownload(self, linkDict, retag=False):

		images = self.fetchImages(linkDict)


		# self.log.info(len(content))

		if images:
			fileN = linkDict['originName']+".zip"
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


	def getLink(self, link):
		try:
			url = self.getDownloadInfo(link)
			self.doDownload(url)
		except urllib.error.URLError:
			self.log.error("Failure retreiving content for link %s", link)
			self.log.error("Traceback: %s", traceback.format_exc())
			self.updateDbEntry(link["sourceUrl"], dlState=-1, downloadPath="ERROR", fileName="ERROR: FAILED")



class HBrowseRetagger(HBrowseContentLoader):

	loggerPath = "Main.Manga.HBrowse.Tag"
	pluginName = "H-Browse Content Re-Tagger"

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	# retreivalThreads = 1

	def retreiveTodoLinksFromDB(self):

		self.log.info( "Fetching items from db...",)

		rows = self.getRowsByValue(dlState=2)

		self.log.info( "Done")
		if not rows:
			return

		items = []
		for item in rows:

			if self.checkDelay(item["retreivalTime"]):
				item["retreivalTime"] = time.gmtime(item["retreivalTime"])
				items.append(item)

		self.log.info( "Have %s new items to process in %sRetagger", len(items), self.tableKey.title())


		return items


	def getLink(self, link):
		try:
			url = self.getDownloadInfo(link)
		except urllib.error.URLError:
			self.log.error("Failure retreiving content for link %s", link)
			self.log.error("Traceback: %s", traceback.format_exc())


if __name__ == "__main__":
	import utilities.testBase as tb

	with tb.testSetup(startObservers=False):

		# run = HBrowseRetagger()
		run = HBrowseContentLoader()

		run.resetStuckItems()
		run.go()
