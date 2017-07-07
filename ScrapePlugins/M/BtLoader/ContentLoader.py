
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

from ScrapePlugins.M.BtLoader.common import checkLogin
from concurrent.futures import ThreadPoolExecutor

import processDownload


class ContentLoader(ScrapePlugins.RetreivalBase.RetreivalBase):




	loggerPath = "Main.Manga.Bt.Cl"
	pluginName = "Batoto Content Retreiver"
	tableKey = "bt"
	dbName = settings.DATABASE_DB_NAME
	tableName = "MangaItems"

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	retreivalThreads = 2

	itemLimit = 500

	def setup(self):
		checkLogin(self.wg)


	def getImage(self, imageUrl, referrer):

		content, handle = self.wg.getpage(imageUrl, returnMultiple=True, addlHeaders={'Referer': referrer})
		if not content or not handle:
			raise ValueError("Failed to retreive image from page '%s'!" % referrer)

		fileN = urllib.parse.unquote(urllib.parse.urlparse(handle.geturl())[2].split("/")[-1])
		fileN = bs4.UnicodeDammit(fileN).unicode_markup
		self.log.info("retreived image '%s' with a size of %0.3f K", fileN, len(content)/1000.0)
		return fileN, content


	def extractFilename(self, inString):
		title, dummy_blurb = inString.rsplit("|", 1)
		# title, chapter = title.rsplit("-", 1)

		# Unescape htmlescaped items in the name/chapter
		ps = html.parser.HTMLParser()
		title = ps.unescape(title)

		vol = None
		chap = None
		volChap = None

		try:
			if " vol " in title.lower():
				title, volChap = title.rsplit(" vol ", 1)
				vol, dummy = volChap.strip().split(" ", 1)
		except ValueError:
			self.log.error("Could not parse volume number from title %s", title)
			traceback.print_exc()


		try:
			if volChap and " ch " in volChap:
				dummy, chap = volChap.rsplit(" ch ", 1)

			elif " ch " in title:
				title, chap = title.rsplit(" ch ", 1)

		except ValueError:
			self.log.error("Could not parse chapter number from title %s", title)
			traceback.print_exc()

		if chap:
			if "Page" in chap:
				chap, dummy = chap.split("Page", 1)

		elif title and "Page" in title:
			title, dummy = title.split("Page", 1)

		title = title.rstrip(" -")
		# haveLookup = nt.haveCanonicalMangaUpdatesName(title)
		# if not haveLookup:
		# 	self.log.warning("Did not find title '%s' in MangaUpdates database!", title)
		title = nt.getCanonicalMangaUpdatesName(title).strip()


		volChap = []

		if vol:
			volChap.append("v{}".format(vol))
		if chap:
			volChap.append("c{}".format(chap))

		chapter = " ".join(volChap)

		return title, chapter.strip()


	def getContainerPages(self, firstPageUrl):

		gid = urllib.parse.urlsplit(firstPageUrl).fragment

		# Korean Webtoons are non-paginated in their default state
		# this breaks shit, so we force paginated mode.
		if not firstPageUrl.endswith("_1_t"):
			firstPageUrl += "_1_t"


		pageUrl = firstPageUrl

		basepage = self.wg.getpage(pageUrl)

		seriesName = "Unknown - ERROR"
		chapterVol = "Unknown - ERROR"

		images = []
		for pgnum in range(1, 9999999):
			ajaxurl = "http://bato.to/areader?id={id}&p={pgnum}&supress_webtoon=t".format(id=gid, pgnum=pgnum)
			extra_headers = {
				"X-Requested-With" : "XMLHttpRequest",
				"Referer"          : "http://bato.to/reader",
			}
			subpage = self.wg.getSoup(ajaxurl, addlHeaders=extra_headers)
			imgtag = subpage.find("img", id='comic_page')
			if not imgtag:
				self.log.warning("No image - Breaking")
				break

			seriesName, chapterVol = self.extractFilename(imgtag['alt'])
			images.append(imgtag['src'])

			pages = subpage.find("select", id='page_select')
			if pgnum + 1 > len(pages.find_all("option")):
				break

		return seriesName, chapterVol, images


	def getLink(self, link):
		sourceUrl = link["sourceUrl"]


		try:
			self.log.info( "Should retreive url - %s", sourceUrl)
			self.updateDbEntry(sourceUrl, dlState=1)

			seriesName, chapterVol, imageUrls = self.getContainerPages(sourceUrl)
			if not seriesName and not chapterVol and not imageUrls:
				self.log.critical("Failure on retreiving content at %s", sourceUrl)
				self.log.critical("Page not found - 404")
				self.updateDbEntry(sourceUrl, dlState=-1)
				return

			self.log.info("Downloading = '%s', '%s'", seriesName, chapterVol)
			dlPath, newDir = self.locateOrCreateDirectoryForSeries(seriesName)

			if link["flags"] == None:
				link["flags"] = ""

			if newDir:
				self.updateDbEntry(sourceUrl, flags=" ".join([link["flags"], "haddir"]))

			chapterNameRaw = " - ".join((seriesName, chapterVol))
			chapterName = nt.makeFilenameSafe(chapterNameRaw)

			fqFName = os.path.join(dlPath, chapterName+" [batoto].zip")

			loop = 1
			while os.path.exists(fqFName):
				fName = "%s [batoto] - (%d).zip" % (chapterName, loop)
				fqFName = os.path.join(dlPath, fName)
				loop += 1
			self.log.info("Saving to archive = %s", fqFName)

			images = []
			for imgUrl in imageUrls:
				self.log.info("Fetching content for item: %s", imgUrl)
				imageName, imageContent = self.getImage(imgUrl, "http://bato.to/reader")

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


			dedupState = processDownload.processDownload(seriesName, fqFName, deleteDups=True, includePHash=False, rowId=link['dbId'])
			self.log.info( "Done")

			filePath, fileName = os.path.split(fqFName)
			self.updateDbEntry(sourceUrl, dlState=2, downloadPath=filePath, fileName=fileName, seriesName=seriesName, originName=chapterNameRaw, tags=dedupState)
			return



		except Exception:
			self.log.critical("Failure on retreiving content at %s", sourceUrl)
			self.log.critical("Traceback = %s", traceback.format_exc())
			self.updateDbEntry(sourceUrl, dlState=-1)



if __name__ == "__main__":
	import utilities.testBase as tb

	with tb.testSetup():

		run = BtContentLoader()
		run.go()
		# got = run.getContainerPages("http://bato.to/reader#be32cd58490fe40a")
		# print(got)
		# run.getMainItems()
		# run.checkLogin()
