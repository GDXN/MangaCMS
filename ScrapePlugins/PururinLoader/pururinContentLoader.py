
# -*- coding: utf-8 -*-

import webFunctions
import os
import os.path

import random
import sys

import nameTools as nt

import runStatus
import time
import urllib.request, urllib.parse, urllib.error
import traceback

import settings
import bs4


import ScrapePlugins.RetreivalDbBase

class PururinContentLoader(ScrapePlugins.RetreivalDbBase.ScraperDbBase):


	wg = webFunctions.WebGetRobust()

	dbName = settings.dbName
	loggerPath = "Main.Pururin.Cl"
	pluginName = "Pururin Content Retreiver"
	tableKey   = "pu"
	urlBase = "http://pururin.com"


	def checkLogin(self):
		acctPage = self.wg.getpage("http://pururin.com/account/home")
		if "You don't have an account!" in acctPage:
			return False
		else:
			return True

	def login(self):
		loginPage = self.wg.getpage("http://pururin.com/account/recover",
				addlHeaders={'Referer': 'http://pururin.com/account/recover'},
				postData={'token': settings.puSettings["accountKey"], "recover-token": "Submit"} )

		if "Success! Welcome back" in loginPage:
			return True

		else:
			return False

	def loginIfNeeded(self):
		self.log.info("Checking login state on Pururin")
		if not self.checkLogin():
			if not self.login():
				self.log.error("Could not log in. Is your account key set?")
		self.log.info("Logged in!")


	def go(self):
		self.loginIfNeeded()
		newLinks = self.retreiveTodoLinksFromDB()
		if newLinks:
			self.processTodoLinks(newLinks)

	def retreiveTodoLinksFromDB(self):

		self.log.info("Fetching items from db...",)

		rows = self.getRowsByValue(dlState=0)
		if not rows:
			self.log.info("No items")
			return
		self.log.info("Done")
		# print(rows)
		items = []
		for row in rows:
			# self.log.info("Row = %s", row)

			items.append(row)  # Actually the contentID
		self.log.info("Have %s new items to retreive in PururinDownloader" % len(items))

		return items


	def processTodoLinks(self, inLinks):

		for contentId in inLinks:
			print("Loopin!")
			try:
				url = self.getDownloadUrl(contentId)
				self.doDownload(url)


				delay = random.randint(5, 30)
			except:
				print("ERROR WAT?")
				traceback.print_exc()
				delay = 1

			return

			for x in range(delay):
				time.sleep(1)
				remaining = delay-x
				sys.stdout.write("\rPururin CL sleeping %d          " % remaining)
				sys.stdout.flush()
				if not runStatus.run:
					self.log.info("Breaking due to exit flag being set")
					return


	def getFileName(self, soup):
		title = soup.find("h1", class_="otitle")
		if not title:
			raise ValueError("Could not find title. Wat?")
		return title.get_text()

	def getCategoryTags(self, soup):
		tagTable = soup.find("table", class_="table-info")

		tags = []

		formatters = {
						"Artist"     : "Artist",
						"Circle"     : "Circles",
						"Parody"     : "Parody",
						"Characters" : "Characters",
						"Contents"   : "",
						"Language"   : "",
						"Scanlator"  : "scanlators",
						"Convention" : "Convention"
					}

		ignoreTags = [
					"Uploader",
					"Pages",
					"Ranking",
					"Rating"]

		catetory = "Unknown?"
		for tr in tagTable.find_all("tr"):
			if len(tr.find_all("td")) != 2:
				continue

			what, values = tr.find_all("td")

			what = what.get_text()
			if what in ignoreTags:
				continue
			elif what == "Category":
				catetory = values.get_text().strip()
				if catetory == "Manga One-shot":
					catetory = "=0= One-Shot"
			elif what in formatters:
				for li in values.find_all("li"):
					tag = " ".join([formatters[what], li.get_text()])
					tag = tag.strip()
					tag = tag.replace("  ", " ")
					tag = tag.replace(" ", "-")
					tags.append(tag)


		return catetory, tags

	def getNote(self, soup):
		note = soup.find("div", class_="gallery-description")
		if note == None:
			note = " "
		else:
			note = note.get_text()

	def getDownloadUrl(self, linkDict):
		sourcePage = linkDict["sourceUrl"]

		self.log.info("Retreiving item: %s", sourcePage)

		# self.updateDbEntry(linkDict["sourceUrl"], dlState=1)


		cont = self.wg.getpage(sourcePage)
		soup = bs4.BeautifulSoup(cont)

		if not soup:
			self.log.critical("No download at url %s! SourceUrl = %s", sourcePage, linkDict["sourceUrl"])
			raise IOError("Invalid webpage")


		fileName = self.getFileName(soup)
		category, tags = self.getCategoryTags(soup)
		note = self.getNote(soup)

		tags = ' '.join(tags)

		linkDict['dirPath'] = os.path.join(settings.puSettings["dlDir"], nt.makeFilenameSafe(category))

		if not os.path.exists(linkDict["dirPath"]):
			os.makedirs(linkDict["dirPath"])
		else:
			self.log.info("Folder Path already exists?: %s", linkDict["dirPath"])


		self.log.info("Folderpath: %s", linkDict["dirPath"])
		#self.log.info(os.path.join())

		dlPage = soup.find("a", class_="btn-download")
		linkDict["dlLink"] = urllib.parse.urljoin(self.urlBase, dlPage["href"])

		self.log.debug("Linkdict = ")
		for key, value in list(linkDict.items()):
			self.log.debug("		%s - %s", key, value)


		if "tags" in linkDict and "note" in linkDict:
			self.updateDbEntry(linkDict["sourceUrl"], tags=tags, note=note, seriesName=category, lastUpdate=time.time())



		return linkDict


	def doDownload(self, linkDict):

		print("Linkdict = ", linkDict)

		gatewayPage = self.wg.getpage(linkDict["dlLink"], addlHeaders={'Referer': linkDict["sourceUrl"]})
		if "Sorry, no more bandwith available. Try again tomorrow." in gatewayPage:
			self.log.warning("Rate limited by Pururun")
			self.updateDbEntry(linkDict["sourceUrl"], dlState=0)
			return

		soup = bs4.BeautifulSoup(gatewayPage)

		link = soup.find("div", class_="download-inset")
		contentUrl = urllib.parse.urljoin(self.urlBase, link.a["href"])


		content, handle = self.wg.getpage(contentUrl, returnMultiple=True, addlHeaders={'Referer': linkDict["dlLink"]})

		# self.log.info(len(content))

		if handle:
			# self.log.info("handle = ", handle)
			# self.log.info("geturl", handle.geturl())
			urlFileN = urllib.parse.unquote(urllib.parse.urlparse(handle.geturl())[2].split("/")[-1])
			urlFileN = bs4.UnicodeDammit(urlFileN).unicode_markup
			urlFileN.encode("utf-8")




			# Pururin is apparently returning "zip.php" for ALL filenames.
			# Blargh
			if urlFileN == "zip.php":
				urlFileN = ".zip"
				fileN = "%s%s" % (linkDict["originName"], urlFileN)
			else:
				self.log.error("Unknown file extension?")
				self.log.error("Unknown file extension?")
				self.log.error("Dict filename = %s", linkDict["originName"])
				self.log.error("URL filename = %s", urlFileN)
				fileN = "%s - %s" % (linkDict["originName"], urlFileN)

			fileN = nt.makeFilenameSafe(fileN)


			# self.log.info("geturl with processing", fileN)
			wholePath = os.path.join(linkDict["dirPath"], fileN)
			self.log.info("Complete filepath: %s", wholePath)

			fp = open(wholePath, "wb")
			fp.write(content)
			fp.close()
			self.log.info("Successfully Saved to path: %s", wholePath)

			if not linkDict["tags"]:
				linkDict["tags"] = ""
			self.updateDbEntry(linkDict["sourceUrl"], dlState=2, downloadPath=linkDict["dirPath"], fileName=fileN, seriesName=linkDict["seriesName"])

			self.conn.commit()

		else:

			self.updateDbEntry(linkDict["sourceUrl"], dlState=-1, downloadPath="ERROR", fileName="ERROR: FAILED")

			# cur.execute('UPDATE djmoe SET downloaded=1 WHERE contentID=?;', (linkDict["sourceUrl"], ))
			# cur.execute('UPDATE djmoe SET dlPath=?, dlName=?, itemTags=?  WHERE contentID=?;', ("ERROR", 'ERROR: FAILED', "N/A", linkDict["contentId"]))
			# self.log.info("fetchall = ", ret.fetchall())
			self.conn.commit()
