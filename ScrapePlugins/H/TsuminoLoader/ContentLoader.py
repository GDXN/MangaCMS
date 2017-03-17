
# -*- coding: utf-8 -*-

import webFunctions
import os
import re
import os.path

import zipfile
import nameTools as nt

import urllib.request, urllib.parse, urllib.error
import traceback

import settings
import bs4
import processDownload
import ScrapePlugins.RetreivalBase

import ScrapePlugins.ScrapeExceptions as ScrapeExceptions

class ContentLoader(ScrapePlugins.RetreivalBase.RetreivalBase):



	dbName = settings.DATABASE_DB_NAME
	loggerPath = "Main.Manga.Tsumino.Cl"
	pluginName = "Tsumino Content Retreiver"
	tableKey   = "ts"
	urlBase = "http://www.tsumino.com/"

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	tableName = "HentaiItems"

	retreivalThreads = 1

	itemLimit = 220

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

	def getDownloadInfo(self, linkDict, retag=False):
		sourcePage = linkDict["sourceUrl"]

		self.log.info("Retreiving item: %s", sourcePage)

		try:
			soup = self.wg.getSoup(sourcePage, addlHeaders={'Referer': self.urlBase})
		except:
			self.log.critical("No download at url %s! SourceUrl = %s", sourcePage, linkDict["sourceUrl"])
			raise IOError("Invalid webpage")


		linkDict['dirPath'] = os.path.join(settings.tsSettings["dlDir"], linkDict['seriesName'])

		if not os.path.exists(linkDict["dirPath"]):
			os.makedirs(linkDict["dirPath"])
		else:
			self.log.info("Folder Path already exists?: %s", linkDict["dirPath"])


		self.log.info("Folderpath: %s", linkDict["dirPath"])
		#self.log.info(os.path.join())


		read_link = soup.find("a", class_='book-read-button', href=re.compile("/read/view", re.IGNORECASE))

		nav_to = urllib.parse.urljoin(self.urlBase, read_link['href'])
		soup = self.wg.getSoup(nav_to, addlHeaders={'Referer': sourcePage})
		if soup.find_all("div", class_="g-recaptcha"):
			raise ScrapeExceptions.LimitedException

		# This is probably brittle
		mid = read_link['href'].split("/")[-1]

		page_params = {
			"q"         : mid,
		}
		addlHeaders = {
			"X-Requested-With" : "XMLHttpRequest",
			"Referer"          : nav_to,
			"Host"             : "www.tsumino.com",
			"Origin"           : "http://www.tsumino.com",
			"Content-Type"     : "application/x-www-form-urlencoded; charset=UTF-8",
			"Cache-Control"    : "no-cache",
			"Pragma"           : "no-cache",
		}

		try:
			jdat = self.wg.getJson("http://www.tsumino.com/Read/Load", postData=page_params, addlHeaders=addlHeaders)
		except Exception as e:
			traceback.format_exc()

			print(e)
			print(e.get_error_page())

			raise RuntimeError



		print("read_link")
		print(read_link)
		print(jdat)


		imageUrls = self.imageUrls(soup)

		# print("Image URLS: ", imageUrls)
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


			chop = len(fileN)-4
			wholePath = "ERROR"
			while 1:

				try:
					fileN = fileN[:chop]+fileN[-4:]
					# self.log.info("geturl with processing", fileN)
					wholePath = os.path.join(linkDict["dirPath"], fileN)
					wholePath = self.insertCountIfFilenameExists(wholePath)
					self.log.info("Complete filepath: %s", wholePath)

					#Write all downloaded files to the archive.

					arch = zipfile.ZipFile(wholePath, "w")
					for imageName, imageContent in images:
						arch.writestr(imageName, imageContent)
					arch.close()

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

			return wholePath

		else:

			self.updateDbEntry(linkDict["sourceUrl"], dlState=-1, downloadPath="ERROR", fileName="ERROR: FAILED")

			return False


	def getLink(self, link):
		try:
			self.updateDbEntry(link["sourceUrl"], dlState=1)
			linkInfo = self.getDownloadInfo(link)
			self.doDownload(linkInfo)
		except IOError:
			self.log.error("Failure retreiving content for link %s", link)
			self.log.error("Traceback: %s", traceback.format_exc())
			self.updateDbEntry(link["sourceUrl"], dlState=-2, downloadPath="ERROR", fileName="ERROR: MISSING")
		except urllib.error.URLError:
			self.log.error("Failure retreiving content for link %s", link)
			self.log.error("Traceback: %s", traceback.format_exc())
			self.updateDbEntry(link["sourceUrl"], dlState=-1, downloadPath="ERROR", fileName="ERROR: FAILED")

	def setup(self):
		self.wg.stepThroughCloudFlare(self.urlBase, titleContains="Tsumino")

if __name__ == "__main__":
	import utilities.testBase as tb

	# with tb.testSetup():
	with tb.testSetup(load=False):

		run = ContentLoader()
		# run.retreivalThreads = 1
		run.resetStuckItems()
		run.go()
		# run.getDownloadInfo("http://www.tsumino.com/Book/Info/27758/1/the-you-behind-the-lens-fakku")
