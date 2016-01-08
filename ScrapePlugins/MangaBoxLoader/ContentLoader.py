

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
import datetime

import urllib.parse
import html.parser
import zipfile
import traceback
import bs4
import re
import json
import ScrapePlugins.RetreivalBase
from mimetypes import guess_extension
from concurrent.futures import ThreadPoolExecutor

import processDownload

class ContentLoader(ScrapePlugins.RetreivalBase.ScraperBase):



	loggerPath = "Main.Manga.Mbx.Cl"
	pluginName = "MangaBox Content Retreiver"
	tableKey = "mbx"
	dbName = settings.DATABASE_DB_NAME
	tableName = "MangaItems"

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	retreivalThreads = 1



	def getImage(self, imageUrl, referrer):

		content, handle = self.wg.getpage(imageUrl, returnMultiple=True, addlHeaders={'Referer': referrer})
		if not content or not handle:
			raise ValueError("Failed to retreive image from page '%s'!" % referrer)

		fileN = urllib.parse.unquote(urllib.parse.urlparse(handle.geturl())[2].split("/")[-1])
		fileN = bs4.UnicodeDammit(fileN).unicode_markup
		self.log.info("retreived image '%s' with a size of %0.3f K", fileN, len(content)/1000.0)

		if not "." in fileN:
			info = handle.info()
			if 'Content-Type' in info:
				tp = info['Content-Type']
				if ";" in tp:
					tp = tp.split(";")[0]
				ext = guess_extension(tp)
				if ext == None:
					ext = "unknown_ftype"
				print(info['Content-Type'], ext)
				fileN += "." + ext
			else:
				fileN += ".jpg"


		return fileN, content



	def getImageUrlsInfo(self, baseUrl):

		soup = self.wg.getSoup(baseUrl)

		container = soup.find("div", class_='swiper-wrapper')
		# print(container)

		imgs = container.find_all("img")


		pages = []
		for item in imgs:
			pages.append(item['src'])

		self.log.info("Found %s pages", len(pages))

		meta = {}

		minfo = soup.find("meta", property="og:title")
		meta['series_name'] = minfo['content'].split(" by ", 1)[0]
		meta['rel_name']    = minfo['content']
		return pages, meta




	def getLink(self, link):


		sourceUrl  = link["sourceUrl"]
		print("Link", link)






		try:
			self.log.info( "Should retreive url - %s", sourceUrl)
			# self.updateDbEntry(sourceUrl, dlState=1)

			imageUrls, meta = self.getImageUrlsInfo(sourceUrl)

			self.updateDbEntry(sourceUrl, seriesName=meta['series_name'])
			seriesName = meta['series_name']

			link["originName"] = meta['rel_name']

			if not imageUrls:
				self.log.critical("Failure on retreiving content at %s", sourceUrl)
				self.log.critical("Page not found - 404")
				# self.updateDbEntry(sourceUrl, dlState=-1)
				return



			self.log.info("Downloading = '%s', '%s' ('%s images)", seriesName, link["originName"], len(imageUrls))
			dlPath, newDir = self.locateOrCreateDirectoryForSeries(seriesName)

			if link["flags"] == None:
				link["flags"] = ""

			if newDir:
				# self.updateDbEntry(sourceUrl, flags=" ".join([link["flags"], "haddir"]))
				self.conn.commit()

			chapterName = nt.makeFilenameSafe(link["originName"])

			fqFName = os.path.join(dlPath, chapterName+" [Comic Zenon].zip")

			loop = 1
			prefix, ext = os.path.splitext(fqFName)
			while os.path.exists(fqFName):
				fqFName = "%s (%d)%s" % (prefix, loop,  ext)
				loop += 1
			self.log.info("Saving to archive = %s", fqFName)

			images = []
			imgCnt = 1
			for imgUrl in imageUrls:
				imageName, imageContent = self.getImage(imgUrl, sourceUrl)
				imageName = "{num:03.0f} - {srcName}".format(num=imgCnt, srcName=imageName)
				imgCnt += 1
				images.append([imageName, imageContent])

				if not runStatus.run:
					self.log.info( "Breaking due to exit flag being set")
					# self.updateDbEntry(sourceUrl, dlState=0)
					return

			self.log.info("Creating archive with %s images", len(images))

			if not images:
				# self.updateDbEntry(sourceUrl, dlState=-1, tags="error-404")
				return

			#Write all downloaded files to the archive.
			arch = zipfile.ZipFile(fqFName, "w")
			for imageName, imageContent in images:
				arch.writestr(imageName, imageContent)
			arch.close()


			dedupState = processDownload.processDownload(seriesName, fqFName, deleteDups=True, includePHash=True)
			self.log.info( "Done")

			filePath, fileName = os.path.split(fqFName)
			# self.updateDbEntry(sourceUrl, dlState=2, downloadPath=filePath, fileName=fileName, tags=dedupState)
			return



		except Exception:
			self.log.critical("Failure on retreiving content at %s", sourceUrl)
			self.log.critical("Traceback = %s", traceback.format_exc())
			# self.updateDbEntry(sourceUrl, dlState=-1)
			raise



if __name__ == '__main__':
	import utilities.testBase as tb

	# with tb.testSetup(startObservers=True):
	with tb.testSetup(startObservers=True):
		cl = ContentLoader()

		# pg = 'http://dynasty-scans.com/chapters/qualia_the_purple_ch16'
		# inMarkup = cl.wg.getpage(pg)
		# cl.getImageUrls(inMarkup, pg)
		cl.go()


		# urls = [
		# 		'http://comic.manga-audition.com/entries/angel-heart-by-tsukasa-hojo-chapter001/',
		# 		'http://comic.manga-audition.com/entries/arte-by-kei-ohkubo-chapter-005/',
		# 		'http://comic.manga-audition.com/entries/ikusa-no-ko_by-tetsuo-hara_chapter003/',
		# 		'http://comic.manga-audition.com/entries/nobo-and-her-by-molico-ross-chapter005/',
		# 		'http://comic.manga-audition.com/entries/nobo-and-her-by-molico-ross-chapter001/',
		# 	]
		# link = {
		# 		'downloadPath'  : None,
		# 		'retreivalTime' : datetime.datetime.now(),
		# 		'lastUpdate'    : 0.0,
		# 		'sourceId'      : None,
		# 		'originName'    : None,
		# 		'tags'          : None,
		# 		'dbId'          : 840370,
		# 		'dlState'       : 0,
		# 		'note'          : None,
		# 		'sourceUrl'     : None,  # Insert here
		# 		'seriesName'    : None,
		# 		'fileName'      : None,
		# 		'flags'         : None
		# 	}

		# for url in urls:
		# 	link['sourceUrl'] = url
		# 	cl.getLink(link)
		# cl.getImageUrls('http://kissmanga.com/Manga/Hanza-Sky/Ch-031-Read-Online?id=225102')


