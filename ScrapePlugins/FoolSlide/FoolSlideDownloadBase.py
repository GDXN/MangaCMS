
import os
import os.path

import nameTools as nt


import urllib.parse
import zipfile
import runStatus
import traceback
import bs4
import re
import json
import ScrapePlugins.RetreivalBase

import processDownload
import abc

class FoolContentLoader(ScrapePlugins.RetreivalBase.ScraperBase):


	@abc.abstractmethod
	def groupName(self):
		return None
	@abc.abstractmethod
	def contentSelector(self):
		return None

	retreivalThreads = 1

	def getImage(self, imageUrl, referrer):

		content, handle = self.wg.getpage(imageUrl, returnMultiple=True, addlHeaders={'Referer': referrer})
		if not content or not handle:
			raise ValueError("Failed to retreive image from page '%s'!" % referrer)

		fileN = urllib.parse.unquote(urllib.parse.urlparse(handle.geturl())[2].split("/")[-1])
		fileN = bs4.UnicodeDammit(fileN).unicode_markup
		self.log.info("retreived image '%s' with a size of %0.3f K", fileN, len(content)/1000.0)
		return fileN, content



	def getImageUrls(self, baseUrl):



		pageCtnt = self.wg.getpage(baseUrl)
		# print("GetImageUrls")
		# print("This series contains mature contents and is meant to be viewed by an adult audience." in pageCtnt)

		if "This series contains mature contents and is meant to be viewed by an adult audience." in pageCtnt:
			self.log.info("Adult check page. Confirming...")
			pageCtnt = self.wg.getpage(baseUrl, postData={"adult": "true"})


		if "This series contains mature contents and is meant to be viewed by an adult audience." in pageCtnt:
			raise ValueError("Wat?")
		soup = bs4.BeautifulSoup(pageCtnt, "lxml")

		container = soup.find(self.contentSelector[0], id=self.contentSelector[1])

		if not container:
			raise ValueError("Unable to find javascript container div '%s'" % baseUrl)

		# If there is a ad div in the content container, it'll mess up the javascript match, so
		# find it, and remove it from the tree.
		container.find('div', id='bottombar').decompose()
		if container.find('div', class_='ads'):
			container.find('div', class_='ads').decompose()

		scriptText = container.script.get_text()
		if not scriptText:
			raise ValueError("No contents in script tag? '%s'" % baseUrl)

		jsonRe = re.compile(r'var pages ?= ?(\[.+?\]);', re.DOTALL)
		jsons = jsonRe.findall(scriptText)

		if not jsons:
			# print("Script = ", container.script)
			raise ValueError("No JSON variable in script! '%s'" % baseUrl)

		arr = json.loads(jsons.pop())

		imageUrls = []

		for item in arr:
			scheme, netloc, path, query, fragment = urllib.parse.urlsplit(item['url'])
			path = urllib.parse.quote(path)
			itemUrl = urllib.parse.urlunsplit((scheme, netloc, path, query, fragment))

			imageUrls.append((item['filename'], itemUrl, baseUrl))

		if not imageUrls:
			raise ValueError("Unable to find contained images on page '%s'" % baseUrl)


		return imageUrls




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

			fqFName = os.path.join(dlPath, chapterName+"["+self.groupName+"].zip")

			loop = 1
			while os.path.exists(fqFName):
				fqFName, ext = os.path.splitext(fqFName)
				fqFName = "%s (%d)%s" % (fqFName, loop,  ext)
				loop += 1
			self.log.info("Saving to archive = %s", fqFName)

			images = []
			for imageName, imgUrl, referrerUrl in imageUrls:
				dummy_imageName, imageContent = self.getImage(imgUrl, referrerUrl)
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


			filePath, fileName = os.path.split(fqFName)
			self.updateDbEntry(sourceUrl, downloadPath=filePath, fileName=fileName)

			dedupState = processDownload.processDownload(seriesName, fqFName, deleteDups=True)
			self.log.info( "Done")

			self.updateDbEntry(sourceUrl, dlState=2, downloadPath=filePath, fileName=fileName, seriesName=seriesName, originName=chapterVol, tags=dedupState)
			return



		except Exception:
			self.log.critical("Failure on retreiving content at %s", sourceUrl)
			self.log.critical("Traceback = %s", traceback.format_exc())
			self.updateDbEntry(sourceUrl, dlState=-1)

