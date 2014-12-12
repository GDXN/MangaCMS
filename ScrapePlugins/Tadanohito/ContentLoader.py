
# -*- coding: utf-8 -*-

import webFunctions
import os
import os.path
import time
import re
import nameTools as nt
import runStatus
import dateutil.parser
import urllib.request, urllib.parse, urllib.error
import traceback

import settings
import random
import processDownload
random.seed()

import ScrapePlugins.RetreivalBase

class ContentLoader(ScrapePlugins.RetreivalBase.ScraperBase):



	dbName = settings.dbName
	loggerPath = "Main.Tadanohito.Cl"
	pluginName = "Tadanohito Content Retreiver"
	tableKey   = "ta"
	urlBase = "http://www.tadanohito.net/"

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	tableName = "HentaiItems"

	retreivalThreads = 1

	shouldCanonize = False

	outOfCredits = False


	def getUploadTime(self, dateStr):
		# ParseDatetime COMPLETELY falls over on "YYYY-MM-DD HH:MM" formatted strings. Not sure why.
		# Anyways, dateutil.parser.parse seems to work ok, so use that.
		updateDate = dateutil.parser.parse(dateStr)
		ret = time.mktime(updateDate.timetuple())

		return ret



	def extractInfo(self, soup):
		ret = {}

		mainDiv = soup.find("div", class_='main-body')
		titles = mainDiv.find_all('font')

		series, title = [item.get_text() for item in titles[-2:]]


		ret['originName'] = title.strip().strip('» 	')
		ret['seriesName'] = series.strip().strip('» 	')

		tds = soup.find_all("td", class_='tbl2')
		for td in tds:
			if "Date Posted:" in td.get_text():
				ret['retreivalTime'] = self.getUploadTime(list(td.strings)[-1])


		return ret




	def getDownloadInfo(self, linkDict, retag=False):
		sourcePage = linkDict["sourceUrl"]
		self.log.info("Retreiving item: %s", sourcePage)

		try:
			soup = self.wg.getSoup(sourcePage, addlHeaders={'Referer': self.urlBase})
		except Exception:
			self.log.critical("No download at url %s! SourceUrl = %s", sourcePage, linkDict["sourceUrl"])
			raise IOError("Invalid webpage")


		ret = self.extractInfo(soup)

		print(ret['retreivalTime'])
		print(linkDict['retreivalTime'])
		return False
		if not ret:
			return False

		linkDict['dirPath'] = os.path.join(settings.tadanohito["dlDir"], linkDict['seriesName'])

		if not os.path.exists(linkDict["dirPath"]):
			os.makedirs(linkDict["dirPath"])

		self.log.info("Folderpath: %s", linkDict["dirPath"])


		linkDict['dlPage'] = self.getDownloadPageUrl(soup)



		return linkDict

	def getDownloadUrl(self, dlPageUrl, referrer):

		soup = self.wg.getSoup(dlPageUrl, addlHeaders={'Referer': referrer})

		if 'Insufficient funds'.lower() in str(soup).lower():
			self.outOfCredits = True
			raise ValueError("Out of credits. Cannot download!")

		if 'Pressing this button will immediately deduct funds' in soup.get_text():
			self.log.info("Accepting download.")
			acceptForm = soup.find('form')
			formPostUrl = acceptForm['action']
			soup = self.wg.getSoup(formPostUrl, addlHeaders={'Referer': referrer}, postData={'dlcheck': 'Download Archive'})
		else:
			self.log.warn("Already accepted download?")



		contLink = soup.find('p', id='continue')
		if not contLink:
			self.log.error("No link found!")
			self.log.error("Page Contents: '%s'", soup)


		downloadUrl = contLink.a['href']+"?start=1"

		return downloadUrl

	def doDownload(self, linkDict, retag=False):

		downloadUrl = self.getDownloadUrl(linkDict['dlPage'], linkDict["sourceUrl"])


		if downloadUrl:


			fCont, fName = self.wg.getFileAndName(downloadUrl)

			# self.log.info(len(content))
			if linkDict['originName'] in fName:
				fileN = fName
			else:
				fileN = '%s - %s.zip' % (linkDict['originName'], fName)
				fileN = fileN.replace('.zip .zip', '.zip')

			fileN = nt.makeFilenameSafe(fileN)

			chop = len(fileN)-4

			wholePath = "ERROR"
			while 1:

				try:
					fileN = fileN[:chop]+fileN[-4:]
					# self.log.info("geturl with processing", fileN)
					wholePath = os.path.join(linkDict["dirPath"], fileN)
					self.log.info("Complete filepath: %s", wholePath)

					#Write all downloaded files to the archive.
					with open(wholePath, "wb") as fp:
						fp.write(fCont)
					self.log.info("Successfully Saved to path: %s", wholePath)
					break
				except IOError:
					chop = chop - 1
					self.log.warn("Truncating file length to %s characters.", chop)




			if not linkDict["tags"]:
				linkDict["tags"] = ""

			self.updateDbEntry(linkDict["sourceUrl"], downloadPath=linkDict["dirPath"], fileName=fileN)

			# Deduper uses the path info for relinking, so we have to dedup the item after updating the downloadPath and fileN
			dedupState = processDownload.processDownload(linkDict["seriesName"], wholePath, pron=True)
			self.log.info( "Done")

			if dedupState:
				self.addTags(sourceUrl=linkDict["sourceUrl"], tags=dedupState)


			# self.updateDbEntry(linkDict["sourceUrl"], dlState=2)
			self.conn.commit()


		else:

			# self.updateDbEntry(linkDict["sourceUrl"], dlState=-1, downloadPath="ERROR", fileName="ERROR: FAILED")

			self.conn.commit()
			return False


	def getLink(self, link):

		try:
			# self.updateDbEntry(link["sourceUrl"], dlState=1)
			linkInfo = self.getDownloadInfo(link)




			if linkInfo:
				self.doDownload(linkInfo)

				sleeptime = random.randint(10,60*15)
			else:
				sleeptime = 5



			self.log.info("Sleeping %s seconds.", sleeptime)
			for dummy_x in range(sleeptime):
				time.sleep(1)
				if not runStatus.run:
					self.log.info( "Breaking due to exit flag being set")
					break

		except urllib.error.URLError:
			self.log.error("Failure retreiving content for link %s", link)
			self.log.error("Traceback: %s", traceback.format_exc())
			self.updateDbEntry(link["sourceUrl"], dlState=-1, downloadPath="ERROR", fileName="ERROR: FAILED")


if __name__ == "__main__":
	import utilities.testBase as tb

	with tb.testSetup(startObservers=False):

		run = ContentLoader()
		run.resetStuckItems()
		run.go()
