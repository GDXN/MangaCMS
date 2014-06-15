
import webFunctions
import settings
import os
import os.path

import nameTools as nt

import time

import urllib.parse
import re
import runStatus
import traceback
import bs4

import ScrapePlugins.RetreivalDbBase

import zipfile
import hashlib


class SkContentLoader(ScrapePlugins.RetreivalDbBase.ScraperDbBase):


	wg = webFunctions.WebGetRobust()
	loggerPath = "Main.Sk.Cl"
	pluginName = "Starkana Content Retreiver"
	tableName = "SkMangaItems"
	dbName = settings.dbName
	urlBase = "http://starkana.com/"

	def retreiveTodoLinksFromDB(self):

		self.log.info( "Fetching items from db...",)

		rows = self.getRowsByValue(dlState=0)

		self.log.info( "Done")
		if not rows:
			return

		items = []
		for item in rows:

			item["retreivalTime"] = time.gmtime(item["retreivalTime"])


			baseNameLower = nt.sanitizeString(item["seriesName"])
			safeBaseName = nt.makeFilenameSafe(item["seriesName"])



			if baseNameLower in nt.dirNameProxy:
				self.log.info( "Have target dir for '%s' Dir = '%s'", baseNameLower, nt.dirNameProxy[baseNameLower]['fqPath'])
				item["targetDir"] = nt.dirNameProxy[baseNameLower]["fqPath"]
			else:
				self.log.info( "Don't have target dir for: %s Using default for: %s, full name = %s", baseNameLower, item["seriesName"], item["originName"])
				if "picked" in item["flags"]:
					targetDir = os.path.join(settings.skSettings["dirs"]['mnDir'], safeBaseName)
				else:
					targetDir = os.path.join(settings.skSettings["dirs"]['mDlDir'], safeBaseName)
				if not os.path.exists(targetDir):
					try:
						os.makedirs(targetDir)
						item["targetDir"] = targetDir
						self.updateDbEntry(item["sourceUrl"],flags=" ".join([item["flags"], "newdir"]))
						self.conn.commit()

						self.conn.commit()
					except OSError:
						self.log.critical("Directory creation failed?")
						self.log.critical(traceback.format_exc())
				else:
					self.log.error("Directory not found in dir-dict, but it exists!")
					self.log.error("Directory-Path: %s", targetDir)
					item["targetDir"] = targetDir

					self.updateDbEntry(item["sourceUrl"],flags=" ".join([item["flags"], "haddir"]))
					self.conn.commit()

			items.append(item)

		self.log.info( "Have %s new items to retreive in SkDownloader" % len(items))


		return items

	# So starkana, in an impressive feat of douchecopterness, inserts an annoying self-promotion image
	# in EVERY manga archive the serve. Furthermore, they insert it in the MIDDLE of the manga.
	# Therefore, this function edits the zip and removes this stupid annoying file.
	def cleanZip(self, zipPath):
		self.log.info("Removing ads from file %s", zipPath)
		if not os.path.exists(zipPath):
			raise ValueError("Trying to clean non-existant file?")

		# MD5 hashes of the images we want to remove (only one, at the moment)
		badHashes = ['17cfa019168817f3297d3640709c4787']
		# MD5 because cryptographic security is not important here

		old_zfp = zipfile.ZipFile(zipPath, "r")

		fileNs = old_zfp.infolist()
		files = []
		for fileInfo in fileNs:

			fctnt = old_zfp.open(fileInfo).read()
			md5 = hashlib.md5()
			md5.update(fctnt)

			# Replace bad image with a text-file with the same name, and an explanation in it.
			if md5.hexdigest() in badHashes:
				self.log.info("File %s was the advert. Removing!", fileInfo.filename)
				fileInfo.filename = fileInfo.filename + ".deleted.txt"
				fctnt  = "This was an advertisement (fuck you, Starkana). It has been automatically removed.\n"
				fctnt += "Don't worry, there are no missing files, despite the gap in the numbering."

			files.append((fileInfo, fctnt))

		old_zfp.close()

		# Now, recreate the zip file without the ad
		new_zfp = zipfile.ZipFile(zipPath, "w")
		for fileInfo, contents in files:
			new_zfp.writestr(fileInfo, contents)
		new_zfp.close()


	def getDownloadUrl(self, containerUrl):
		page = self.wg.getpage(containerUrl)
		soup = bs4.BeautifulSoup(page)

		link = soup.find("a", href=re.compile(".*download.*"))
		print("Link = ", link["href"])
		if link:
			return link["href"]

		return None

	def getLinkFile(self, fileUrl):
		pgctnt, pghandle = self.wg.getpage(fileUrl, returnMultiple = True)
		pageUrl = pghandle.geturl()
		hName = urllib.parse.urlparse(pageUrl)[2].split("/")[-1]
		self.log.info( "HName: %s", hName, )
		self.log.info( "Size = %s", len(pgctnt))


		return pgctnt, hName


	def getLink(self, link):
		sourceUrl, originFileName = link["sourceUrl"], link["originName"]

		self.log.info( "Should retreive: %s, url - %s", originFileName, sourceUrl)

		self.updateDbEntry(sourceUrl, dlState=1)

		fileUrl = self.getDownloadUrl(sourceUrl)



		self.conn.commit()
		try:
			content, hName = self.getLinkFile(fileUrl)
		except:
			self.log.error("Unrecoverable error retreiving content %s", link)
			self.log.error("Traceback: %s", traceback.format_exc())

			self.updateDbEntry(sourceUrl, dlState=-1)
			return

		# print("Content type = ", type(content))

		# Clean Annoying, bullshit self-promotion in names
		hName = hName.replace("[starkana.com]_", "").replace("[starkana.com]", "")

		fName = "%s - %s" % (originFileName, hName)
		fName = nt.makeFilenameSafe(fName)

		fqFName = os.path.join(link["targetDir"], fName)
		self.log.info( "SaveName = %s", fqFName)

		loop = 1
		while os.path.exists(fqFName):
			fName = "%s - (%d) - %s" % (originFileName, loop,  hName)
			fqFName = os.path.join(link["targetDir"], fName)
			loop += 1
		self.log.info( "Writing file")

		filePath, fileName = os.path.split(fqFName)

		try:
			with open(fqFName, "wb") as fp:
				fp.write(content)
		except TypeError:
			self.log.error("Failure trying to retreive content from source %s", sourceUrl)
			self.updateDbEntry(sourceUrl, dlState=-1, downloadPath=filePath, fileName=fileName)
			return
		#self.log.info( filePath)

		self.cleanZip(fqFName)
		self.log.info( "Done")

		self.updateDbEntry(sourceUrl, dlState=2, downloadPath=filePath, fileName=fileName)
		return


	def fetchLinkList(self, linkList):
		try:
			for link in linkList:

				self.getLink(link)

				if not runStatus.run:
					self.log.info( "Breaking due to exit flag being set")
					break

		except:
			self.log.critical("Exception!")
			traceback.print_exc()
			self.log.critical(traceback.format_exc())


	def processTodoLinks(self, links):
		if links:

			# Multithreading goes here, if I decide I want it at some point
			self.fetchLinkList(links)


	def go(self):

		todo = self.retreiveTodoLinksFromDB()
		if not runStatus.run:
			return
		self.processTodoLinks(todo)
