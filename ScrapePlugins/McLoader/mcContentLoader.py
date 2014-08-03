
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
import ScrapePlugins.RetreivalDbBase

from concurrent.futures import ThreadPoolExecutor

import archCleaner

class McContentLoader(ScrapePlugins.RetreivalDbBase.ScraperDbBase):


	archCleaner = archCleaner.ArchCleaner()

	wg = webFunctions.WebGetRobust()
	loggerPath = "Main.Mc.Cl"
	pluginName = "MangaCow Content Retreiver"
	tableKey = "mc"
	dbName = settings.dbName
	tableName = "MangaItems"

	retreivalThreads = 2

	def retreiveTodoLinksFromDB(self):

		self.log.info( "Fetching items from db...",)

		rows = self.getRowsByValue(dlState=0)

		self.log.info( "Done")
		if not rows:
			return

		items = []
		for item in rows:

			item["retreivalTime"] = time.gmtime(item["retreivalTime"])


			items.append(item)

		self.log.info( "Have %s new items to retreive in BtDownloader" % len(items))


		items = sorted(items, key=lambda k: k["retreivalTime"], reverse=True)
		return items


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
		soup = bs4.BeautifulSoup(pageCtnt)

		selector = soup.find("select", class_="cbo_wpm_pag")

		if not selector:
			raise ValueError("Unable to find contained images on page '%s'" % baseUrl)

		pageNumbers = []
		for value in selector.find_all("option"):
			pageNumbers.append(int(value.get_text())-1)


		if not pageNumbers:
			raise ValueError("Unable to find contained images on page '%s'" % baseUrl)



		pageUrls = []
		for pageNo in pageNumbers:
			pageUrls.append("{baseUrl}{num}/".format(baseUrl=baseUrl, num=pageNo))

		# print("PageUrls", pageUrls)
		imageUrls = []

		for pageUrl in pageUrls:


			pageCtnt = self.wg.getpage(pageUrl)

			soup = bs4.BeautifulSoup(pageCtnt)

			imageContainer = soup.find("div", class_="prw")
			url = imageContainer.img["src"]
			# print("Urls - ", (url, pageUrl))
			imageUrls.append((url, pageUrl))


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

			self.log.info("Downloading = '%s', '%s'", seriesName, chapterVol)
			dlPath, newDir = self.locateOrCreateDirectoryForSeries(seriesName)

			if link["flags"] == None:
				link["flags"] = ""

			if newDir:
				self.updateDbEntry(sourceUrl, flags=" ".join([link["flags"], "haddir"]))
				self.conn.commit()

			chapterName = nt.makeFilenameSafe(chapterVol)

			fqFName = os.path.join(dlPath, chapterName+".zip")

			loop = 1
			while os.path.exists(fqFName):
				fName = "%s - (%d).zip" % (chapterName, loop)
				fqFName = os.path.join(dlPath, fName)
				loop += 1
			self.log.info("Saving to archive = %s", fqFName)

			images = []
			for imgUrl, referrerUrl in imageUrls:
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


			dedupState = self.archCleaner.processNewArchive(fqFName, deleteDups=True)
			self.log.info( "Done")

			filePath, fileName = os.path.split(fqFName)
			self.updateDbEntry(sourceUrl, dlState=2, downloadPath=filePath, fileName=fileName, seriesName=seriesName, originName=chapterVol, tags=dedupState)
			return



		except Exception:
			self.log.critical("Failure on retreiving content at %s", sourceUrl)
			self.log.critical("Traceback = %s", traceback.format_exc())
			self.updateDbEntry(sourceUrl, dlState=-1)


	def fetchLinkList(self, linkList):
		try:
			for link in linkList:
				if link is None:
					self.log.error("One of the items in the link-list is none! Wat?")
					continue

				ret = self.getLink(link)


				if not runStatus.run:
					self.log.info( "Breaking due to exit flag being set")
					break

		except:
			self.log.critical("Exception!")
			traceback.print_exc()
			self.log.critical(traceback.format_exc())


	def processTodoLinks(self, links):
		if links:

			def iter_baskets_from(items, maxbaskets=3):
				'''generates evenly balanced baskets from indexable iterable'''
				item_count = len(items)
				baskets = min(item_count, maxbaskets)
				for x_i in range(baskets):
					yield [items[y_i] for y_i in range(x_i, item_count, baskets)]

			linkLists = iter_baskets_from(links, maxbaskets=self.retreivalThreads)

			with ThreadPoolExecutor(max_workers=self.retreivalThreads) as executor:

				for linkList in linkLists:
					executor.submit(self.fetchLinkList, linkList)

				executor.shutdown(wait=True)




	def go(self):

		todo = self.retreiveTodoLinksFromDB()
		if not runStatus.run:
			return
		self.processTodoLinks(todo)
