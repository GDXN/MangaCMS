
import webFunctions
import settings
import os
import os.path

import nameTools as nt


import urllib.parse
import zipfile
import runStatus
import traceback
import bs4
import ScrapePlugins.RetreivalBase


import processDownload

class ContentLoader(ScrapePlugins.RetreivalBase.ScraperBase):



	loggerPath = "Main.Kw.Cl"
	pluginName = "Kawaii-Scans Content Retreiver"
	tableKey = "kw"
	dbName = settings.DATABASE_DB_NAME
	tableName = "MangaItems"

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	retreivalThreads = 4

	urlBase = "http://kawaii.ca/reader/"

	def getImage(self, imageUrl, referrer):

		content, handle = self.wg.getpage(imageUrl, returnMultiple=True, addlHeaders={'Referer': referrer})
		if not content or not handle:
			raise ValueError("Failed to retreive image from page '%s'!" % referrer)

		fileN = urllib.parse.unquote(urllib.parse.urlparse(handle.geturl())[2].split("/")[-1])
		fileN = bs4.UnicodeDammit(fileN).unicode_markup
		self.log.info("retreived image '%s' with a size of %0.3f K", fileN, len(content)/1000.0)
		return fileN, content




	def getImagePages(self, chapBaseUrl):
		soup = self.wg.getSoup(chapBaseUrl)
		ret = []

		pager = soup.find("div", class_="pager")
		spans = pager.find_all('span')
		if len(spans) != 3:
			self.log.error("Invalid span items! Page: '%s'", chapBaseUrl)
			return ret

		dummy_series, dummy_chapter, pages = spans

		for page in pages.find_all('option'):

			pageUrl = '{chapUrl}/{pageno}'.format(chapUrl=chapBaseUrl, pageno=page['value'])
			ret.append(pageUrl)


		return ret

	def getImageUrls(self, chapUrl):

		pages = {}

		pageBases = self.getImagePages(chapUrl)

		for pageBase in pageBases:
			soup = self.wg.getSoup(pageBase)

			image = soup.find("img", class_='picture')

			# I'm.... actually not sure how the url they're using
			# works in-browser, since it doesn't appear to resolve out properly
			# when inspected in the browser debugger, but works outside of it.
			# Anyways, just hack it together
			imUrl = urllib.parse.urljoin(self.urlBase, urllib.parse.quote(image['src']))
			pages[imUrl] = pageBase

		self.log.info("Found %s pages", len(pages))

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

			fqFName = os.path.join(dlPath, chapterName+" [Kawaii-Scans].zip")

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

if __name__ == '__main__':
	import utilities.testBase as tb
	with tb.testSetup(startObservers=True):
		cl = ContentLoader()
		print("CL", cl)
		# print(cl.retreiveTodoLinksFromDB())
		# print(cl.getImageUrls('http://kawaii.ca/reader/Himawari-san/Chapter_1'))
		cl.go()
		# cl.getLink('http://www.webtoons.com/viewer?titleNo=281&episodeNo=3')


