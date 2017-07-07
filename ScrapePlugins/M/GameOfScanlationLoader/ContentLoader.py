

import logSetup
import runStatus

import bs4
import nameTools as nt
import os
import os.path
import processDownload
import ScrapePlugins.RetreivalBase
import settings
import traceback
import urllib.parse
import webFunctions
import zipfile

class ContentLoader(ScrapePlugins.RetreivalBase.RetreivalBase):

	retreivalThreads = 1

	loggerPath = "Main.Manga.GoS.Cl"
	pluginName = "Game of Scanlation Scans Content Retreiver"
	tableKey = "gos"
	dbName = settings.DATABASE_DB_NAME

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	tableName = "MangaItems"

	urlBase    = "https://gameofscanlation.moe/"
	seriesBase = "https://gameofscanlation.moe/projects/"

	def getImage(self, imageUrl, referrer):

		content, handle = self.wg.getpage(imageUrl, returnMultiple=True, addlHeaders={'Referer': referrer})
		if not content or not handle:
			raise ValueError("Failed to retreive image from page '%s'!" % referrer)

		fileN = urllib.parse.unquote(urllib.parse.urlparse(handle.geturl())[2].split("/")[-1])
		fileN = bs4.UnicodeDammit(fileN).unicode_markup
		self.log.info("retreived image '%s' with a size of %0.3f K", fileN, len(content)/1000.0)
		return fileN, content

	def getImageUrls(self, baseUrl):
		pages = set()

		soup = self.wg.getSoup(baseUrl)


		imagesDiv = soup.find('div', class_='chapterPages')
		images = imagesDiv.find_all('img', class_='avatar')

		pageno = 1
		for image in images:
			src = image['src']
			if "pagespeed" in src:
				scheme, netloc, path, query, fragment = urllib.parse.urlsplit(src)
				root, filename = os.path.split(path)
				filename = filename.split(".pagespeed.")[0]
				if filename.startswith("x"):
					filename = filename[1:]
				path = os.path.join(root, filename)
				src = urllib.parse.urlunsplit((scheme, netloc, path, query, fragment))

			pages.add((pageno, src))
			pageno += 1


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

			chapterName = nt.makeFilenameSafe(chapterVol)

			fqFName = os.path.join(dlPath, chapterName+" [GameOfScanlation.moe].zip")

			loop = 1
			while os.path.exists(fqFName):
				fqFName, ext = os.path.splitext(fqFName)
				fqFName = "%s (%d)%s" % (fqFName, loop,  ext)
				loop += 1
			self.log.info("Saving to archive = %s", fqFName)

			images = []
			for imgNum, imgUrl in imageUrls:
				imageName, imageContent = self.getImage(imgUrl, referrer=sourceUrl)
				images.append([imgNum, imageName, imageContent])

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
			for imgNum, imageName, imageContent in images:
				arch.writestr("{:03} - {}".format(imgNum, imageName), imageContent)
			arch.close()


			dedupState = processDownload.processDownload(seriesName, fqFName, deleteDups=True, rowId=link['dbId'])
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
		# cl.go()

		sourceUrl = "https://gameofscanlation.moe/projects/unbalance-triangle/chapter-32-2.1036/"

		imageUrls = cl.getImageUrls(sourceUrl)

		for url in imageUrls:
			print(url)
		images = []
		for imgNum, imgUrl in imageUrls:
			imageName, imageContent = cl.getImage(imgUrl, referrer=sourceUrl)
			print(imgNum, imgUrl, imageName)
			images.append([imgNum, imageName, imageContent])



