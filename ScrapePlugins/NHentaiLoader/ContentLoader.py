
# -*- coding: utf-8 -*-

import webFunctions
import os
import os.path

import zipfile
import nameTools as nt

import urllib.request, urllib.parse, urllib.error
import traceback

import settings
import bs4
import processDownload


import ScrapePlugins.RetreivalBase

class ContentLoader(ScrapePlugins.RetreivalBase.ScraperBase):



	dbName = settings.dbName
	loggerPath = "Main.NHentai.Cl"
	pluginName = "NHentai Content Retreiver"
	tableKey   = "nh"
	urlBase = "http://nhentai.net/"

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	tableName = "HentaiItems"

	retreivalThreads = 6

	shouldCanonize = False

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
			thumbUrl = link.img['src']
			if not "t." in thumbUrl[-6:]:
				raise ValueError("Url is not a thumb? = '%s'" % thumbUrl)
			else:
				imgUrl = thumbUrl[:-6] + thumbUrl[-6:].replace("t.", '.')

			imgUrl   = urllib.parse.urljoin(self.urlBase, imgUrl)

			ret.append((imgUrl, referrer))

		return ret

	def getDownloadInfo(self, linkDict, retag=False):
		sourcePage = linkDict["sourceUrl"]

		self.log.info("Retreiving item: %s", sourcePage)



		try:
			soup = self.wg.getSoup(sourcePage, addlHeaders={'Referer': self.urlBase})
		except:
			self.log.critical("No download at url %s! SourceUrl = %s", sourcePage, linkDict["sourceUrl"])
			raise IOError("Invalid webpage")


		linkDict['dirPath'] = os.path.join(settings.nhSettings["dlDir"], linkDict['seriesName'])

		if not os.path.exists(linkDict["dirPath"]):
			os.makedirs(linkDict["dirPath"])
		else:
			self.log.info("Folder Path already exists?: %s", linkDict["dirPath"])


		self.log.info("Folderpath: %s", linkDict["dirPath"])
		#self.log.info(os.path.join())


		imageUrls = self.imageUrls(soup)


		linkDict["dlLinks"] = imageUrls



		self.log.debug("Linkdict = ")
		for key, value in list(linkDict.items()):
			self.log.debug("		%s - %s", key, value)


		return linkDict

	def getImage(self, imageUrl, referrer):

		content, handle = self.wg.getpage(imageUrl, returnMultiple=True, addlHeaders={'Referer': referrer})
		if not content or not handle:
			raise ValueError("Failed to retreive image from page '%s'!" % referrer)

		fileN = urllib.parse.unquote(urllib.parse.urlparse(handle.geturl())[2].split("/")[-1])
		fileN = bs4.UnicodeDammit(fileN).unicode_markup
		self.log.info("retreived image '%s' with a size of %0.3f K", fileN, len(content)/1000.0)
		return fileN, content



	def fetchImages(self, linkDict):

		images = []
		for imgUrl, referrerUrl in linkDict["dlLinks"]:
			images.append(self.getImage(imgUrl, referrerUrl))

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


			dedupState = processDownload.processDownload(linkDict["seriesName"], wholePath, pron=True)
			self.log.info( "Done")


			if dedupState:
				self.addTags(sourceUrl=linkDict["sourceUrl"], tags=dedupState)

			self.updateDbEntry(linkDict["sourceUrl"], dlState=2, downloadPath=linkDict["dirPath"], fileName=fileN)

			self.conn.commit()
			return wholePath

		else:

			self.updateDbEntry(linkDict["sourceUrl"], dlState=-1, downloadPath="ERROR", fileName="ERROR: FAILED")

			self.conn.commit()
			return False


	def getLink(self, link):
		try:
			self.updateDbEntry(link["sourceUrl"], dlState=1)
			linkInfo = self.getDownloadInfo(link)
			self.doDownload(linkInfo)
		except urllib.error.URLError:
			self.log.error("Failure retreiving content for link %s", link)
			self.log.error("Traceback: %s", traceback.format_exc())
			self.updateDbEntry(link["sourceUrl"], dlState=-1, downloadPath="ERROR", fileName="ERROR: FAILED")


if __name__ == "__main__":
	import utilities.testBase as tb

	with tb.testSetup(startObservers=False):

		run = ContentLoader()
		run.resetStuckItems()
		run.go()
