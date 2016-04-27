
# -*- coding: utf-8 -*-

import webFunctions
import os
import os.path
import time
import re
import nameTools as nt
import runStatus
import urllib.request, urllib.parse, urllib.error
import traceback

import settings
import random
import processDownload
random.seed()

import ScrapePlugins.RetreivalBase

class ContentLoader(ScrapePlugins.RetreivalBase.ScraperBase):



	dbName = settings.DATABASE_DB_NAME
	loggerPath = "Main.Manga.SadPanda.Cl"
	pluginName = "SadPanda Content Retreiver"
	tableKey   = "sp"
	urlBase = "http://exhentai.org/"

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	tableName = "HentaiItems"

	retreivalThreads = 1

	shouldCanonize = False

	outOfCredits = False

	def getTags(self, sourceUrl, inSoup):

		tagDiv = inSoup.find('div', id='taglist')

		formatters = {
						'character:'   : 'character',
						'parody:'      : "parody",
						'artist:'      : "artist",
						'group:'       : "group",

					}

		tagList = []
		for row in tagDiv.find_all("tr"):
			tagType, tags = row.find_all("td")

			tagType = tagType.get_text().strip()
			if tagType in formatters:
				prefix = formatters[tagType]
			else:
				prefix = ''

			for tag in tags.find_all('div'):
				tag = '%s %s' % (prefix, tag.get_text())
				while tag.find("  ") + 1:
					tag = tag.replace("  ", " ")
				tag = tag.strip()
				tag = tag.replace(" ", "-")
				tagList.append(tag)


		for tag in settings.sadPanda['sadPandaExcludeTags']:
			if tag in tagList:
				self.log.info("Blocked item! Deleting row from database.")
				self.log.info("Item tags = '%s'", tagList)
				self.log.info("Blocked tag = '%s'", tag)
				self.deleteRowsByValue(sourceUrl=sourceUrl)
				return False

		# We sometimes want to do compound blocks.
		# For example, if something is tagged 'translated', but not 'english', it's
		# probably not english, but not the original item either (assuming you want
		# either original items, or the english tranlsation).
		# Therefore, if settings.sadPanda['excludeCompoundTags'][n][0] is in the taglist,
		# and not settings.sadPanda['excludeCompoundTags'][n][1], we skip the item.
		for exclude, when in settings.sadPanda['excludeCompoundTags']:
			if exclude in tagList:
				if not when in tagList:
					self.log.info("Blocked item! Deleting row from database.")
					self.log.info("Item tags = '%s'", tagList)
					self.log.info("Triggering tags: = '%s', '%s'", exclude, when)
					self.deleteRowsByValue(sourceUrl=sourceUrl)
					return False


		tags = " ".join(tagList)
		self.log.info("Adding tags: '%s'", tags)
		self.addTags(sourceUrl=sourceUrl, tags=tags)
		return True


	def getDownloadPageUrl(self, inSoup):
		dlA = inSoup.find('a', onclick=re.compile('archiver.php'))

		clickAction = dlA['onclick']
		clickUrl = re.search("(http://exhentai.org/archiver.php.*)'", clickAction)
		return clickUrl.group(1)


	def getDownloadInfo(self, linkDict, retag=False):
		sourcePage = linkDict["sourceUrl"]
		self.log.info("Retreiving item: %s", sourcePage)

		# self.log.info("Linkdict = ")
		# for key, value in list(linkDict.items()):
		# 	self.log.info("		%s - %s", key, value)

		try:
			soup = self.wg.getSoup(sourcePage, addlHeaders={'Referer': self.urlBase})
		except Exception as e:

			self.log.critical("No download at url %s! SourceUrl = %s", sourcePage, linkDict["sourceUrl"])
			for line in traceback.format_exc().split("\n"):
				self.log.critical(""+line)

			raise IOError("Invalid webpage")

		if "This gallery has been removed, and is unavailable." in soup.get_text():
			self.log.info("Gallery deleted. Removing.")
			self.deleteRowsByValue(sourceUrl=sourcePage)
			return False

		ret = self.getTags(sourcePage, soup)
		if not ret:
			return False

		linkDict['dirPath'] = os.path.join(settings.sadPanda["dlDir"], linkDict['seriesName'])

		if not os.path.exists(linkDict["dirPath"]):
			os.makedirs(linkDict["dirPath"])

		self.log.info("Folderpath: %s", linkDict["dirPath"])


		linkDict['dlPage'] = self.getDownloadPageUrl(soup)



		return linkDict

	def getDownloadUrl(self, dlPageUrl, referrer):

		soup = self.wg.getSoup(dlPageUrl, addlHeaders={'Referer': referrer})

		if 'Insufficient funds'.lower() in str(soup).lower():
			self.outOfCredits = True
			raise ValueError("Out of credits. Cannot download!")

		if 'Pressing this button will immediately deduct funds' in soup.get_text():
			self.log.info("Accepting download.")
			acceptForm = soup.find('form')
			formPostUrl = acceptForm['action']
			soup = self.wg.getSoup(formPostUrl, addlHeaders={'Referer': referrer}, postData={'dlcheck': 'Download Archive'})
		else:
			self.log.warn("Already accepted download?")



		contLink = soup.find('p', id='continue')
		if not contLink:
			self.log.error("No link found!")
			self.log.error("Page Contents: '%s'", soup)


		downloadUrl = contLink.a['href']+"?start=1"

		return downloadUrl

	def doDownload(self, linkDict, retag=False):

		downloadUrl = self.getDownloadUrl(linkDict['dlPage'], linkDict["sourceUrl"])


		if downloadUrl:


			fCont, fName = self.wg.getFileAndName(downloadUrl)

			# self.log.info(len(content))
			if linkDict['originName'] in fName:
				fileN = fName
			else:
				fileN = '%s - %s.zip' % (linkDict['originName'], fName)
				fileN = fileN.replace('.zip .zip', '.zip')

			fileN = nt.makeFilenameSafe(fileN)

			chop = len(fileN)-4

			wholePath = "ERROR"
			while 1:

				try:
					fileN = fileN[:chop]+fileN[-4:]
					# self.log.info("geturl with processing", fileN)
					wholePath = os.path.join(linkDict["dirPath"], fileN)
					self.log.info("Complete filepath: %s", wholePath)

					#Write all downloaded files to the archive.
					with open(wholePath, "wb") as fp:
						fp.write(fCont)
					self.log.info("Successfully Saved to path: %s", wholePath)
					break
				except IOError:
					chop = chop - 1
					self.log.warn("Truncating file length to %s characters.", chop)




			if not linkDict["tags"]:
				linkDict["tags"] = ""

			self.updateDbEntry(linkDict["sourceUrl"], downloadPath=linkDict["dirPath"], fileName=fileN)

			# Deduper uses the path info for relinking, so we have to dedup the item after updating the downloadPath and fileN
			dedupState = processDownload.processDownload(linkDict["seriesName"], wholePath, pron=True)
			self.log.info( "Done")

			if dedupState:
				self.addTags(sourceUrl=linkDict["sourceUrl"], tags=dedupState)


			self.updateDbEntry(linkDict["sourceUrl"], dlState=2)
			self.conn.commit()


		else:

			self.updateDbEntry(linkDict["sourceUrl"], dlState=-1, downloadPath="ERROR", fileName="ERROR: FAILED")

			self.conn.commit()
			return False


	def getLink(self, link):
		if self.outOfCredits:
			self.log.warn("Out of credits. Skipping!")
			return
		try:
			self.updateDbEntry(link["sourceUrl"], dlState=1)
			linkInfo = self.getDownloadInfo(link)
			if linkInfo:
				self.doDownload(linkInfo)

				sleeptime = random.randint(10,60*5)
			else:
				sleeptime = 5

			self.log.info("Sleeping %s seconds.", sleeptime)
			for dummy_x in range(sleeptime):
				time.sleep(1)
				if not runStatus.run:
					self.log.info( "Breaking due to exit flag being set")
					break

		except Exception:
			self.log.error("Failure retreiving content for link %s", link)
			self.log.error("Traceback: %s", traceback.format_exc())
			self.updateDbEntry(link["sourceUrl"], dlState=-1, downloadPath="ERROR", fileName="ERROR: FAILED")


if __name__ == "__main__":
	import utilities.testBase as tb

	with tb.testSetup(startObservers=False):

		run = ContentLoader()
		run.resetStuckItems()
		run.go()
