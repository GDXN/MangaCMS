
import webFunctions
import settings
import os
import os.path

import nameTools as nt

import time

import urllib.parse
import html.parser
import re
import runStatus
import traceback
import bs4

import ScrapePlugins.RetreivalDbBase


import archCleaner

class BtContentLoader(ScrapePlugins.RetreivalDbBase.ScraperDbBase):


	archCleaner = archCleaner.ArchCleaner()

	wg = webFunctions.WebGetRobust()
	loggerPath = "Main.Bt.Cl"
	pluginName = "Batoto Content Retreiver"
	tableKey = "bt"
	dbName = settings.dbName


	def retreiveTodoLinksFromDB(self):

		self.log.info( "Fetching items from db...",)

		rows = self.getRowsByValue(dlState=0)

		self.log.info( "Done")
		if not rows:
			return

		# Anyways, limit the maximum items/hour to 50 items
		rows = rows[4:9]

		items = []
		for item in rows:

			item["retreivalTime"] = time.gmtime(item["retreivalTime"])


			items.append(item)

		self.log.info( "Have %s new items to retreive in BtDownloader" % len(items))


		items = sorted(items, key=lambda k: k["retreivalTime"], reverse=True)
		return items

	def getImage(self, containerPageUrl):
		pass

	def extractFilename(self, inString):
		title, dummy_blurb = inString.rsplit("|", 1)
		title, chapter = title.rsplit("-", 1)

		# Unescape htmlescaped items in the name/chapter
		ps = html.parser.HTMLParser()
		title = ps.unescape(title)
		chapter = ps.unescape(chapter)
		vol = None
		chap = None

		try:
			if "ch" in chapter.lower():
				dummy, chap = chapter.lower().split("ch", 1)
				chap, dummy = chap.strip().split(" ", 1)
				chap = int(chap)
		except ValueError:
			self.log.error("Could not parse chapter number from title %s", chapter)

		try:
			if "vol" in chapter.lower():
				dummy, vol = chapter.lower().split("vol", 1)
				vol, dummy = vol.strip().split(" ", 1)
				vol = int(vol)
		except ValueError:
			self.log.error("Could not parse volume number from title %s", chapter)

		haveLookup = nt.haveCanonicalMangaUpdatesName(title)
		if not haveLookup:
			self.log.warning("Did not find title '%s' in MangaUpdates database!", title)
		title = nt.getCanonicalMangaUpdatesName(title).strip()

		volChap = []

		if vol:
			volChap.append("v{0:02d}".format(vol))
		if chap:
			volChap.append("c{0:03d}".format(chap))

		chapter = " ".join(volChap)

		return " - ".join((title, chapter))


	def getContainerPages(self, firstPageUrl):
		soup = self.wg.getpage(firstPageUrl, soup=True)

		title = soup.find("meta", property="og:title")
		title = title["content"]

		fileName = self.extractFilename(title)

		selector = soup.find("select", attrs={'name':'page_select'})
		if not selector:
			return False

		pages = selector.find_all("option")
		pages = [page["value"] for page in pages]
		print("len", len(pages))


		return fileName, pages


	def getLink(self, link):
		sourceUrl = link["sourceUrl"]

		fileName, imageUrls = self.getContainerPages(sourceUrl)

		for imgUrl in imageUrls:
			imageName, imageContent = self.getImage(imgUrl)

		# self.updateDbEntry(sourceUrl, dlState=1)
		# self.conn.commit()


		# self.log.info( "Should retreive: %s, url - %s", originFileName, sourceUrl)


		# fileUrl = self.getDownloadUrl(sourceUrl)
		# if fileUrl is None:
		# 	self.log.warning("Could not find url!")
		# 	self.deleteRowsByValue(sourceUrl=sourceUrl)
		# 	return

		# if fileUrl == "http://starkana.com/download/manga/":
		# 	self.log.warning("File doesn't actually exist because starkana are a bunch of douchecanoes!")
		# 	self.deleteRowsByValue(sourceUrl=sourceUrl)
		# 	return

		# try:
		# 	content, hName = self.getLinkFile(fileUrl)
		# except:
		# 	self.log.error("Unrecoverable error retreiving content %s", link)
		# 	self.log.error("Traceback: %s", traceback.format_exc())

		# 	self.updateDbEntry(sourceUrl, dlState=-1)
		# 	return

		# # print("Content type = ", type(content))

		# # Clean Annoying, bullshit self-promotion in names
		# hName = hName.replace("[starkana.com]_", "").replace("[starkana.com]", "")

		# # And fix %xx crap
		# hName = urllib.parse.unquote(hName)

		# fName = "%s - %s" % (originFileName, hName)
		# fName = nt.makeFilenameSafe(fName)

		# fqFName = os.path.join(link["targetDir"], fName)
		# self.log.info( "SaveName = %s", fqFName)

		# loop = 1
		# while os.path.exists(fqFName):
		# 	fName = "%s - (%d) - %s" % (originFileName, loop,  hName)
		# 	fqFName = os.path.join(link["targetDir"], fName)
		# 	loop += 1
		# self.log.info( "Writing file")

		# filePath, fileName = os.path.split(fqFName)

		# if type(content) is str and "You have been limit reached." in content:
		# 	self.log.warning("Hit rate-limiting error. Breaking")
		# 	self.updateDbEntry(sourceUrl, dlState=0)
		# 	return "Limited"

		# try:
		# 	with open(fqFName, "wb") as fp:
		# 		fp.write(content)
		# except TypeError:
		# 	self.log.error("Failure trying to retreive content from source %s", sourceUrl)
		# 	return
		# #self.log.info( filePath)

		# dedupState = self.archCleaner.processNewArchive(fqFName, deleteDups=True)
		# self.log.info( "Done")

		# self.updateDbEntry(sourceUrl, dlState=2, downloadPath=filePath, fileName=fileName, tags=dedupState)
		# return


	def fetchLinkList(self, linkList):
		try:
			for link in linkList:
				if link is None:
					self.log.error("One of the items in the link-list is none! Wat?")
					continue

				ret = self.getLink(link)
				if ret == "Limited":
					break


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
