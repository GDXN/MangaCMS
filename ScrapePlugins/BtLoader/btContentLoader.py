
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

import processDownload

class BtContentLoader(ScrapePlugins.RetreivalDbBase.ScraperDbBase):




	loggerPath = "Main.Bt.Cl"
	pluginName = "Batoto Content Retreiver"
	tableKey = "bt"
	dbName = settings.dbName
	tableName = "MangaItems"

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	retreivalThreads = 8

	def retreiveTodoLinksFromDB(self):

		self.log.info( "Fetching items from db...",)

		rows = self.getRowsByValue(dlState=0)

		self.log.info( "Done")
		if not rows:
			return

		# Anyways, limit the maximum items/hour to 500 items
		rows = rows[:500]

		items = []
		for item in rows:

			item["retreivalTime"] = time.gmtime(item["retreivalTime"])


			items.append(item)

		self.log.info( "Have %s new items to retreive in BtDownloader" % len(items))


		items = sorted(items, key=lambda k: k["retreivalTime"], reverse=True)
		return items


	def getImageFromPage(self, containerPageUrl):

		soup = self.wg.getSoup(containerPageUrl)


		img = soup.find("img", id="comic_page")
		if not img:
			raise ValueError("Could not find image on page '%s'!" % containerPageUrl)
		imgUrl = img["src"]

		return self.getImage(imgUrl, containerPageUrl)

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
		haveLookup = nt.haveCanonicalMangaUpdatesName(title)
		if not haveLookup:
			self.log.warning("Did not find title '%s' in MangaUpdates database!", title)
		title = nt.getCanonicalMangaUpdatesName(title).strip()


		volChap = []

		if vol:
			volChap.append("v{}".format(vol))
		if chap:
			volChap.append("c{}".format(chap))

		chapter = " ".join(volChap)

		return title, chapter


	def getContainerPages(self, firstPageUrl):

		# Korean Webtoons are non-paginated in their default state
		# this breaks shit, so we force paginated mode.
		if not firstPageUrl.endswith("/1"):
			firstPageUrl += "/1"

		pageCtnt = self.wg.getpage(firstPageUrl)
		soup = bs4.BeautifulSoup(pageCtnt)
		title = soup.find("meta", property="og:title")
		title = title["content"]

		if 'alt="File not found"' in pageCtnt:
			return False, False, False, False

		seriesName, chapterVol = self.extractFilename(title)

		selector = soup.find("select", attrs={'name':'page_select'})
		if selector:

			pages = selector.find_all("option")
			pages = [page["value"] for page in pages]
			self.log.info("Item has %s pages.", len(pages))

			return seriesName, chapterVol, pages, False

		if not selector and "Want to see this chapter per page instead?" in pageCtnt:
			self.log.info("It's a webcomic.")

			contentDiv = soup.find("div", attrs={'id':'content', 'class':'clearfix'})
			images = contentDiv.find_all("img", src=re.compile(r'img[0-9]?\.bato\.to/comics/[0-9][0-9][0-9][0-9]'))

			images = [image["src"] for image in images]
			return seriesName, chapterVol, images, True


		raise ValueError("Unable to find contained images on page '%s'" % firstPageUrl)



	def getLink(self, link):
		sourceUrl = link["sourceUrl"]


		try:
			self.log.info( "Should retreive url - %s", sourceUrl)
			self.updateDbEntry(sourceUrl, dlState=1)

			seriesName, chapterVol, imageUrls, directImageLinks = self.getContainerPages(sourceUrl)
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
				self.conn.commit()

			chapterNameRaw = " - ".join((seriesName, chapterVol))
			chapterName = nt.makeFilenameSafe(chapterNameRaw)

			fqFName = os.path.join(dlPath, chapterName+" [batoto].zip")

			loop = 1
			while os.path.exists(fqFName):
				fName = "%s - (%d).zip" % (chapterName, loop)
				fqFName = os.path.join(dlPath, fName)
				loop += 1
			self.log.info("Saving to archive = %s", fqFName)

			images = []
			for imgUrl in imageUrls:
				if directImageLinks:
					imageName, imageContent = self.getImage(imgUrl, sourceUrl)
				else:
					imageName, imageContent = self.getImageFromPage(imgUrl)

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


			dedupState = processDownload.processDownload(seriesName, fqFName, deleteDups=True, includePHash=True)
			self.log.info( "Done")

			filePath, fileName = os.path.split(fqFName)
			self.updateDbEntry(sourceUrl, dlState=2, downloadPath=filePath, fileName=fileName, seriesName=seriesName, originName=chapterNameRaw, tags=dedupState)
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

			# Multithreading goes here, if I decide I want it at some point



	def go(self):

		todo = self.retreiveTodoLinksFromDB()
		if not runStatus.run:
			return
		self.processTodoLinks(todo)
