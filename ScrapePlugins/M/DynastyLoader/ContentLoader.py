

import logSetup
import runStatus
if __name__ == "__main__":
	runStatus.preloadDicts = False


import webFunctions
import settings
import os
import os.path

import nameTools as nt

import time

import urllib.parse
import html.parser
import zipfile
import traceback
import bs4
import re
import json
import ScrapePlugins.RetreivalBase

from concurrent.futures import ThreadPoolExecutor

import processDownload

class ContentLoader(ScrapePlugins.RetreivalBase.ScraperBase):



	loggerPath = "Main.Manga.Dy.Cl"
	pluginName = "Dynasty Scans Content Retreiver"
	tableKey = "dy"
	dbName = settings.DATABASE_DB_NAME
	tableName = "MangaItems"

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	retreivalThreads = 3

	urlBase = "http://dynasty-scans.com/"

	def getImage(self, imageUrl, referrer):

		content, handle = self.wg.getpage(imageUrl, returnMultiple=True, addlHeaders={'Referer': referrer})
		if not content or not handle:
			raise ValueError("Failed to retreive image from page '%s'!" % referrer)

		fileN = urllib.parse.unquote(urllib.parse.urlparse(handle.geturl())[2].split("/")[-1])
		fileN = bs4.UnicodeDammit(fileN).unicode_markup
		self.log.info("retreived image '%s' with a size of %0.3f K", fileN, len(content)/1000.0)
		return fileN, content



	def getImageUrls(self, inMarkup, baseUrl):

		pages = {}


		jsonRe = re.compile(r'var pages = (\[.*?\]);')

		pg = jsonRe.findall(inMarkup)
		if len(pg) != 1:
			self.log.error("Erroring page '%s'", baseUrl)
			raise ValueError("Page has more then one json section?")

		images = json.loads(pg.pop())

		for item in images:
			imgurl = urllib.parse.urljoin(baseUrl, item['image'])
			pages[imgurl] = baseUrl

		self.log.info("Found %s pages", len(pages))

		return pages


	def getSeries(self, markup):
		soup = bs4.BeautifulSoup(markup, "lxml")
		title = soup.find("h3", id='chapter-title')

		if title.b.find('a'):
			title = title.b.a.get_text()

		else:
			title = title.b.get_text()

		title = nt.getCanonicalMangaUpdatesName(title)
		print("Title '%s'" % title)
		return title





	def getLink(self, link):


		sourceUrl  = link["sourceUrl"]
		chapterVol = link["originName"]

		inMarkup = self.wg.getpage(sourceUrl)

		seriesName = self.getSeries(inMarkup)


		try:
			self.log.info( "Should retreive url - %s", sourceUrl)
			self.updateDbEntry(sourceUrl, dlState=1)

			imageUrls = self.getImageUrls(inMarkup, sourceUrl)
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

			fqFName = os.path.join(dlPath, chapterName+" [DynastyScans].zip")

			loop = 1
			prefix, ext = os.path.splitext(fqFName)
			while os.path.exists(fqFName):
				fqFName = "%s (%d)%s" % (prefix, loop,  ext)
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

if __name__ == '__main__':
	import utilities.testBase as tb

	with tb.testSetup():
		cl = ContentLoader()

		# pg = 'http://dynasty-scans.com/chapters/qualia_the_purple_ch16'
		# inMarkup = cl.wg.getpage(pg)
		# cl.getImageUrls(inMarkup, pg)
		cl.go()
		# cl.getLink('http://www.webtoons.com/viewer?titleNo=281&episodeNo=3')


