
import webFunctions
import settings
import os
import os.path

import nameTools as nt

import time

import urllib.parse
import html.parser
import zipfile
import runStatus
import traceback
import bs4
import re
import json
import ScrapePlugins.RetreivalBase

from concurrent.futures import ThreadPoolExecutor

import processDownload

class LmContentLoader(ScrapePlugins.RetreivalBase.ScraperBase):



	loggerPath = "Main.Lm.Cl"
	pluginName = "RedHawk Scans Content Retreiver"
	tableKey = "lm"
	dbName = settings.dbName
	tableName = "MangaItems"

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	retreivalThreads = 3

	urlBase = "http://lonemanga.com/"

	def getImage(self, imageUrl, referrer):

		content, handle = self.wg.getpage(imageUrl, returnMultiple=True, addlHeaders={'Referer': referrer})
		if not content or not handle:
			raise ValueError("Failed to retreive image from page '%s'!" % referrer)

		fileN = urllib.parse.unquote(urllib.parse.urlparse(handle.geturl())[2].split("/")[-1])
		fileN = bs4.UnicodeDammit(fileN).unicode_markup
		self.log.info("retreived image '%s' with a size of %0.3f K", fileN, len(content)/1000.0)
		return fileN, content



	def getImageUrls(self, baseUrl):


		currentUrl = baseUrl+"/0"
		pages = {}

		while 1:
			pageCtnt = self.wg.getpage(currentUrl)
			soup = bs4.BeautifulSoup(pageCtnt)
			imageTr = soup.find('tr', attrs={'id': 'imageWrapper'})

			image = imageTr.img['src']

			if image in pages:
				break

			pages[image] = currentUrl

			if not imageTr.a:
				break

			nextPage = imageTr.a['href']
			if not baseUrl in nextPage:
				break


			currentUrl = nextPage

		print("Found ", len(pages), "pages")

		return pages




	def getLink(self, link):
		sourceUrl  = link["sourceUrl"]
		seriesName = link["seriesName"]
		chapterVol = link["originName"]


		try:
			self.log.info( "Should retreive url - %s", sourceUrl)
			self.updateDbEntry(sourceUrl, dlState=1)

			imageUrls = self.getImageUrls(sourceUrl)
			if not imageUrls:
				self.log.critical("Failure on retreiving content at %s", sourceUrl)
				self.log.critical("Page not found - 404")
				self.updateDbEntry(sourceUrl, dlState=-1)
				return



			self.log.info("Downloading = '%s', '%s' ('%s images)", seriesName, chapterVol, len(imageUrls))
			dlPath, newDir = self.locateOrCreateDirectoryForSeries(seriesName)

			if link["flags"] == None:
				link["flags"] = ""

			if newDir:
				self.updateDbEntry(sourceUrl, flags=" ".join([link["flags"], "haddir"]))
				self.conn.commit()

			chapterName = nt.makeFilenameSafe(chapterVol)

			fqFName = os.path.join(dlPath, chapterName+" [LoneManga].zip")

			loop = 1
			while os.path.exists(fqFName):
				fqFName, ext = os.path.splitext(fqFName)
				fqFName = "%s (%d)%s" % (fqFName, loop,  ext)

				loop += 1
			self.log.info("Saving to archive = %s", fqFName)

			images = []
			for imgUrl, referrerUrl in imageUrls.items():
				imageName, imageContent = self.getImage(imgUrl, referrerUrl)
				images.append([imageName, imageContent])

				if not runStatus.run:
					self.log.info( "Breaking due to exit flag being set")
					self.updateDbEntry(sourceUrl, dlState=0)
					return

			self.log.info("Creating archive with %s images", len(images))

			if not images:
				self.updateDbEntry(sourceUrl, dlState=-1, seriesName=seriesName, originName=chapterVol, tags="error-404")
				return

			#Write all downloaded files to the archive.
			arch = zipfile.ZipFile(fqFName, "w")
			for imageName, imageContent in images:
				arch.writestr(imageName, imageContent)
			arch.close()


			dedupState = processDownload.processDownload(seriesName, fqFName, deleteDups=True)
			self.log.info( "Done")

			filePath, fileName = os.path.split(fqFName)
			self.updateDbEntry(sourceUrl, dlState=2, downloadPath=filePath, fileName=fileName, seriesName=seriesName, originName=chapterVol, tags=dedupState)
			return



		except Exception:
			self.log.critical("Failure on retreiving content at %s", sourceUrl)
			self.log.critical("Traceback = %s", traceback.format_exc())
			self.updateDbEntry(sourceUrl, dlState=-1)

