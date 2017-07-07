
# -*- coding: utf-8 -*-

import re

import os
import os.path
import sys

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

import ScrapePlugins.RetreivalBase

class ContentLoader(ScrapePlugins.RetreivalBase.RetreivalBase):




	dbName = settings.DATABASE_DB_NAME
	loggerPath = "Main.Manga.DoujinOnline.Cl"
	pluginName = "DoujinOnline Content Retreiver"
	tableKey   = "dol"
	urlBase = "https://doujinshi.online/"

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	tableName = "HentaiItems"


	retreivalThreads = 2

	itemLimit = 220


	def getFileName(self, soup):
		title = soup.find("h1")
		if not title:
			raise ValueError("Could not find title. Wat?")
		return title.get_text().strip()


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


	def format_tag(self, tag_raw):

		tag = tag_raw.strip()
		while "  " in tag:
			tag = tag.replace("  ", " ")
		tag = tag.strip().replace(" ", "-")
		return tag.lower()

	def getCategoryTags(self, soup):
		tagdiv = soup.find("div", class_='tagbox')
		tagps = tagdiv.find_all("p")

		tags = []

		category = "Unknown?"
		artist_str = "unknown artist"

		formatters = {
						"tags"       : "",
						"artist"     : "artist",
						"group"      : "group",
						"characters" : "character",
						"language"   : "language",
						"type"       : "type",
					}


		for item in tagps:
			what = item.get_text(strip=True).split(":")[0].lower().strip()
			if not what in formatters:
				self.log.error("Unknown metadata key: %s", what)
				continue

			tags_strings = item.find_all("a", rel='tag')
			tags_strings = [tmp.get_text(strip=True) for tmp in tags_strings]
			tags_strings = [tmp for tmp in tags_strings if tmp != "N/A"]

			if tags_strings and what == 'artist':
				artist_str = tags_strings[0]

			for tag_str in tags_strings:
				tag = " ".join([formatters[what], tag_str])
				tag = self.format_tag(tag)
				tags.append(tag)

		cat = soup.find("a", rel="category")

		if cat:
			category = cat.get_text(strip=True)

		return category, tags, artist_str

	def getDownloadInfo(self, linkDict, soup):

		infoSection = soup.find("div", id='infobox')


		category, tags, artist = self.getCategoryTags(infoSection)
		tags = ' '.join(tags)
		linkDict['artist'] = artist
		linkDict['title'] = self.getFileName(infoSection)
		linkDict['dirPath'] = os.path.join(settings.djOnSettings["dlDir"], nt.makeFilenameSafe(category))

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

	def getImages(self, linkDict, soup):

		print("getImage", linkDict)

		postdiv = soup.find('div', id="post")
		if not postdiv.script:
			self.log.error("No script tag on page!")
			return []
		scripttxt = postdiv.script.get_text()
		scriptre = re.compile(r'var js_array = (\[.*?),\];//', flags=re.IGNORECASE)
		match = scriptre.search(scripttxt)
		if not match:
			self.log.error("No image array on page!")
			return []

		# Translate annoying javascript literal to something json compatible.
		data_array = match.group(1) + "]"
		imageurls = json.loads(data_array)



		if not imageurls:
			return []
		referrer = linkDict['sourceUrl']

		images = []
		count = 1
		for imageurl in imageurls:
			garbagen, imgf = self.getImage(imageurl, referrer)
			intn = "%04d.jpeg" % count
			images.append((intn, imgf))
			count += 1

		return images


	def getLink(self, linkDict):

		try:
			self.updateDbEntry(linkDict["sourceUrl"], dlState=1)

			sourcePage = linkDict["sourceUrl"]
			self.log.info("Retreiving item: %s", sourcePage)
			soup = self.wg.getSoup(sourcePage, addlHeaders={'Referer': 'https://doujinshi.online/'})
			if not soup:
				self.log.critical("No download at url %s! SourceUrl = %s", sourcePage, linkDict["sourceUrl"])
				raise IOError("Invalid webpage")

			linkDict = self.getDownloadInfo(linkDict, soup)
			images = self.getImages(linkDict, soup)

			title  = linkDict['title']
			artist = linkDict['artist']


		except webFunctions.ContentError:
			self.updateDbEntry(linkDict["sourceUrl"], dlState=-2, downloadPath="ERROR", fileName="ERROR: FAILED")

		if images and title:
			fileN = title+" - "+artist+".zip"
			fileN = nt.makeFilenameSafe(fileN)


			# self.log.info("geturl with processing", fileN)
			wholePath = os.path.join(linkDict["dirPath"], fileN)
			wholePath = self.insertCountIfFilenameExists(wholePath)
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
			dedupState = processDownload.processDownload(None, wholePath, pron=True, deleteDups=True, includePHash=True, rowId=linkDict['dbId'])
			self.log.info( "Done")

			if dedupState:
				self.addTags(sourceUrl=linkDict["sourceUrl"], tags=dedupState)


			self.updateDbEntry(linkDict["sourceUrl"], dlState=2)

			return wholePath

		else:

			self.updateDbEntry(linkDict["sourceUrl"], dlState=-1, downloadPath="ERROR", fileName="ERROR: FAILED")
			return False



if __name__ == "__main__":
	import utilities.testBase as tb

	with tb.testSetup(load=False):

		run = ContentLoader()
		# run.getLink({'sourceUrl':'https://doujinshi.online/graffiti/'})
		# run.getLink({'sourceUrl':'https://doujinshi.online/hishoku-yuusha-plus/'})
		# run.getDownloadInfo({'sourceUrl':'https://doujinshi.online/cherry-pink-na-kougai-souguu/'})
		run.go()

