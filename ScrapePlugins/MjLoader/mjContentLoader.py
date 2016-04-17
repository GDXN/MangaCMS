
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
import ScrapePlugins.RetreivalBase
import psycopg2


import processDownload

class MjContentLoader(ScrapePlugins.RetreivalBase.ScraperBase):

	loggerPath = "Main.Manga.Mj.Cl"
	pluginName = "MangaJoy Content Retreiver"
	tableKey = "mj"
	dbName = settings.DATABASE_DB_NAME
	tableName = "MangaItems"

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	urlBase = "http://mangajoy.com/"

	retreivalThreads = 6
	itemLimit = 500

	# Mangajoy does recompress. Arrrgh.
	PHASH_THRESH = 6

	def checkDelay(self, inTime):
		return inTime < (time.time() - 60*30)


	def getImage(self, imageUrl, referrer):

		content, handle = self.wg.getpage(imageUrl, returnMultiple=True, addlHeaders={'Referer': referrer})
		if not content or not handle:
			raise ValueError("Failed to retreive image from page '%s'!" % referrer)

		fileN = urllib.parse.unquote(urllib.parse.urlparse(handle.geturl())[2].split("/")[-1])
		fileN = bs4.UnicodeDammit(fileN).unicode_markup
		self.log.info("retreived image '%s' with a size of %0.3f K", fileN, len(content)/1000.0)
		return fileN, content

	def getImgUrlFromPage(self, pageSoup):

		imgDiv = pageSoup.find("div", class_='prw')
		images = imgDiv.find_all("img")
		images = [image for image in images if ("manga-joy" in image['src'] or "mangajoy" in image['src'])]
		for image in images:
			print(image)
		if len(images) != 1:
			for image in images:
				print("Image", image)
			raise ValueError("Too many images found on page!")

		imgUrl = images[0]["src"]
		return imgUrl

	def getImageUrls(self, firstPageUrl):

		pageCtnt = self.wg.getpage(firstPageUrl)
		soup = bs4.BeautifulSoup(pageCtnt, "lxml")

		if 'alt="File not found"' in pageCtnt:
			return []

		imgUrl = self.getImgUrlFromPage(soup)

		selectDiv = soup.find("div", class_="wpm_nav_rdr")
		selector = selectDiv.find("select", style="width:45px")

		imUrls = set([imgUrl])

		if selector:

			pages = selector.find_all("option")

			# Because people are insane, sometimes a single manga has both png and jpeg files.
			# Since this means that we cannot just sequentially guess the image
			# URLs from the number of pages, we have to actually walk every image page in the manga
			# to get all the proper image URLs.

			scanPages = ["{base}{cnt}/".format(base=firstPageUrl, cnt=page["value"]) for page in pages]
			for page in scanPages:
				pageCtnt = self.wg.getpage(page)
				soup = bs4.BeautifulSoup(pageCtnt, "lxml")
				imUrls.add(self.getImgUrlFromPage(soup))


			self.log.info("Item has %s pages.", len(imUrls))

			return imUrls



		raise ValueError("Unable to find contained images on page '%s'" % firstPageUrl)



	def getLink(self, link):
		sourceUrl = link["sourceUrl"]
		seriesName = link['seriesName']
		chapterNameRaw = link['originName']

		try:
			self.log.info( "Should retreive url - %s", sourceUrl)
			self.updateDbEntry(sourceUrl, dlState=1)

			imageUrls = self.getImageUrls(sourceUrl)

			if not imageUrls:
				self.log.critical("Failure on retreiving content at %s", sourceUrl)
				self.log.critical("Page not found - 404")
				self.updateDbEntry(sourceUrl, dlState=-1)
				return

			self.log.info("Downloading = '%s', '%s'", seriesName, chapterNameRaw)
			dlPath, newDir = self.locateOrCreateDirectoryForSeries(seriesName)

			if link["flags"] == None:
				link["flags"] = ""

			if newDir:
				self.updateDbEntry(sourceUrl, flags=" ".join([link["flags"], "haddir"]))
				self.conn.commit()

			chapterName = nt.makeFilenameSafe(chapterNameRaw)

			fqFName = os.path.join(dlPath, chapterName+"[MangaJoy].zip")

			loop = 1
			while os.path.exists(fqFName):
				fqFName, ext = os.path.splitext(fqFName)
				fqFName = "%s (%d)%s" % (fqFName, loop,  ext)
				loop += 1
			self.log.info("Saving to archive = %s", fqFName)

			images = []
			for imgUrl in imageUrls:
				imageName, imageContent = self.getImage(imgUrl, sourceUrl)

				images.append([imageName, imageContent])

				if not runStatus.run:
					self.log.info( "Breaking due to exit flag being set")
					self.updateDbEntry(sourceUrl, dlState=0)
					return

			self.log.info("Creating archive with %s images", len(images))

			if not images:
				self.updateDbEntry(sourceUrl, dlState=-1, seriesName=seriesName, originName=chapterNameRaw, tags="error-404")
				return

			#Write all downloaded files to the archive.
			arch = zipfile.ZipFile(fqFName, "w")
			for imageName, imageContent in images:
				arch.writestr(imageName, imageContent)
			arch.close()


			dedupState = processDownload.processDownload(seriesName, fqFName, deleteDups=True, includePHash=True, phashThresh=self.PHASH_THRESH)
			self.log.info( "Done")

			filePath, fileName = os.path.split(fqFName)
			self.updateDbEntry(sourceUrl, dlState=2, downloadPath=filePath, fileName=fileName, seriesName=seriesName, originName=chapterNameRaw, tags=dedupState)
			return


		except psycopg2.OperationalError:
			self.log.info("Database issue?")
			raise

		except Exception:
			self.log.critical("Failure on retreiving content at %s", sourceUrl)
			self.log.critical("Traceback = %s", traceback.format_exc())
			self.updateDbEntry(sourceUrl, dlState=-1)




	def go(self):

		todo = self.retreiveTodoLinksFromDB()
		if not runStatus.run:
			return
		self.processTodoLinks(todo)


if __name__ == "__main__":
	import utilities.testBase as tb

	with tb.testSetup(startObservers=False):
		run = MjContentLoader()
		run.go()
