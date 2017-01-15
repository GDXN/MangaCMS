
# -*- coding: utf-8 -*-

import re

import os
import os.path

import random
import json
import sys
import zipfile

import time
import pprint
import urllib.parse
import traceback

import bs4


import runStatus
runStatus.preloadDicts = False
import nameTools as nt
import webFunctions
import settings

import processDownload

import ScrapePlugins.RetreivalDbBase

class PururinContentLoader(ScrapePlugins.RetreivalDbBase.ScraperDbBase):




	dbName = settings.DATABASE_DB_NAME
	loggerPath = "Main.Manga.Pururin.Cl"
	pluginName = "Pururin Content Retreiver"
	tableKey   = "pu"
	urlBase = "http://pururin.us"

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	tableName = "HentaiItems"



	def getFileName(self, soup):
		title = soup.find("h1", class_="otitle")
		if not title:
			raise ValueError("Could not find title. Wat?")
		return title.get_text()


	def imageUrls(self, soup):
		thumbnailDiv = soup.find("div", id="thumbnail-container")

		ret = []

		for link in thumbnailDiv.find_all("a", class_='gallerythumb'):

			referrer = urllib.parse.urljoin(self.urlBase, link['href'])
			if hasattr(link, "data-src"):
				thumbUrl = link.img['data-src']
			else:
				thumbUrl = link.img['src']

			if not "t." in thumbUrl[-6:]:
				raise ValueError("Url is not a thumb? = '%s'" % thumbUrl)
			else:
				imgUrl = thumbUrl[:-6] + thumbUrl[-6:].replace("t.", '.')

			imgUrl   = urllib.parse.urljoin(self.urlBase, imgUrl)
			imgUrl = imgUrl.replace("//t.", "//i.")

			ret.append((imgUrl, referrer))

		return ret



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


	def getDownloadInfo(self, linkDict):
		sourcePage = linkDict["sourceUrl"]

		self.log.info("Retreiving item: %s", sourcePage)

		self.updateDbEntry(linkDict["sourceUrl"], dlState=1)

		soup = self.wg.getSoup(sourcePage, addlHeaders={'Referer': 'http://pururin.us/'})

		if not soup:
			self.log.critical("No download at url %s! SourceUrl = %s", sourcePage, linkDict["sourceUrl"])
			raise IOError("Invalid webpage")

		category, tags = self.getCategoryTags(soup)
		note = self.getNote(soup)
		tags = ' '.join(tags)

		linkDict['title'] = self.getFileName(soup)
		linkDict['dirPath'] = os.path.join(settings.puSettings["dlDir"], nt.makeFilenameSafe(category))

		if not os.path.exists(linkDict["dirPath"]):
			os.makedirs(linkDict["dirPath"])
		else:
			self.log.info("Folder Path already exists?: %s", linkDict["dirPath"])

		self.log.info("Folderpath: %s", linkDict["dirPath"])

		self.log.debug("Linkdict = ")
		for key, value in list(linkDict.items()):
			self.log.debug("		%s - %s", key, value)


		if tags:
			self.log.info("Adding tag info %s", tags)

			self.addTags(sourceUrl=linkDict["sourceUrl"], tags=tags)
		if note:
			self.log.info("Adding note %s", note)
			self.updateDbEntry(linkDict["sourceUrl"], note=note)


		read_url = soup.find("a", text=re.compile("Read Online", re.IGNORECASE))
		spage = urllib.parse.urljoin(self.urlBase, read_url['href'])

		linkDict["spage"] = spage

		self.updateDbEntry(linkDict["sourceUrl"], seriesName=category, lastUpdate=time.time())

		return linkDict

	def getImage(self, imageUrl, referrer):

		content, handle = self.wg.getpage(imageUrl, returnMultiple=True, addlHeaders={'Referer': referrer})
		if not content or not handle:
			raise ValueError("Failed to retreive image from page '%s'!" % referrer)

		fileN = urllib.parse.unquote(urllib.parse.urlparse(handle.geturl())[2].split("/")[-1])
		fileN = bs4.UnicodeDammit(fileN).unicode_markup
		self.log.info("retreived image '%s' with a size of %0.3f K", fileN, len(content)/1000.0)
		return fileN, content

	def getImages(self, linkDict):
		soup = self.wg.getSoup(linkDict['spage'], addlHeaders={'Referer': linkDict["sourceUrl"]})
		scripts = "\n".join([scrt.get_text() for scrt in soup.find_all("script")])
		dat_arr = None
		for line in [t.strip() for t in scripts.split("\n") if t.strip()]:
			if line.startswith("var d = "):
				# Trin off the assignment and semicoln
				data = line[8:-1]
				dat_arr = json.loads(data)
		if not dat_arr:
			return []

		images = []
		for dummy_key, value in dat_arr.items():
			images.append(self.getImage(value['chapter_image'], linkDict['spage']))

		return images


	def doDownload(self, linkDict):

		images = self.getImages(linkDict)
		title = linkDict['title']

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



	def processTodoLinks(self, inLinks):

		for contentId in inLinks:
			print("Loopin!")
			try:
				url = self.getDownloadInfo(contentId)
				self.doDownload(url)

				delay = random.randint(5, 30)
			except RuntimeError:
				raise
			except Exception:
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



	def go(self):

		self.wg.stepThroughCloudFlare(self.urlBase, titleContains="Pururin")

		newLinks = self.retreiveTodoLinksFromDB()
		if newLinks:
			self.processTodoLinks(newLinks)


if __name__ == "__main__":
	import utilities.testBase as tb

	with tb.testSetup(startObservers=False, load=False):

		run = PururinContentLoader()
		run.go()

