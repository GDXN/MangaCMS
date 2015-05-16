
# -*- coding: utf-8 -*-

import webFunctions
import os
import os.path
import time
import calendar
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



	dbName = settings.DATABASE_DB_NAME
	loggerPath = "Main.Manga.Tadanohito.Cl"
	pluginName = "Tadanohito Content Retreiver"
	tableKey   = "ta"
	urlBase = "http://www.tadanohito.net/"

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	tableName = "HentaiItems"

	retreivalThreads = 1

	shouldCanonize = False

	outOfCredits = False




	# -----------------------------------------------------------------------------------
	# Login Management tools
	# -----------------------------------------------------------------------------------


	def checkLogin(self):

		getPage = self.wg.getpage(r"http://www.tadanohito.net/news.php")
		if "Welcome, {username}".format(username=settings.tadanohito["login"]) in getPage:
			self.log.info("Still logged in")
			return
		else:
			self.log.info("Whoops, need to get Login cookie")

		logondict = {
			"user_name"   : settings.tadanohito["login"],
			"user_pass"   : settings.tadanohito["passWd"],
			"remember_me" : "y",
			"login"       : "Login"
			}


		getPage = self.wg.getpage(r"http://www.tadanohito.net/news.php", postData=logondict)
		if "Welcome, {username}".format(username=settings.tadanohito["login"]) in getPage:
			self.log.info("Logged in successfully!")
		elif "You are now logged in as:" in getPage:
			self.log.error("Login failed!")

		self.wg.saveCookies()

	def setup(self):
		self.checkLogin()


	# -----------------------------------------------------------------------------------
	# The scraping parts
	# -----------------------------------------------------------------------------------



	def getUploadTime(self, dateStr):
		# ParseDatetime COMPLETELY falls over on "YYYY-MM-DD HH:MM" formatted strings. Not sure why.
		# Anyways, dateutil.parser.parse seems to work ok, so use that.
		updateDate = dateutil.parser.parse(dateStr)
		ret = calendar.timegm(updateDate.timetuple())

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

	def getDownloadPageUrl(self, soup, sourceUrl):
		dlForms = soup.find_all('form', action='file.php')
		for form in dlForms:
			if 'D I R E C T  D O W N L O A D' in [tag['value'] for tag in form.find_all('input')]:


				ret = {}
				for inTag in form.find_all('input'):
					if 'name' in inTag.attrs and 'value' in inTag.attrs:

						ret[inTag['name']] = inTag['value']

				query = urllib.parse.urlencode(ret)
				url = urllib.parse.urljoin(sourceUrl, form['action'])

				urlParts = list(urllib.parse.urlsplit(url))
				urlParts[3] = query
				url = urllib.parse.urlunsplit(urlParts)

				return url


	def getDownloadInfo(self, linkDict, retag=False):
		sourcePage = linkDict["sourceUrl"]

		self.log.info("Retreiving item: %s", sourcePage)

		try:
			soup = self.wg.getSoup(sourcePage, addlHeaders={'Referer': self.urlBase})
		except Exception:
			self.log.critical("No download at url %s! SourceUrl = %s", sourcePage, linkDict["sourceUrl"])
			raise IOError("Invalid webpage")


		ret = self.extractInfo(soup)

		if not ret:
			return False

		if not 'retreivalTime' in ret:
			return False


		self.updateDbEntry(linkDict["sourceUrl"],
					seriesName=ret['seriesName'],
					originName=ret['originName'],
					retreivaltime=ret['retreivalTime'])



		ret["sourceUrl"] = linkDict["sourceUrl"]


		ret['dirPath'] = os.path.join(settings.tadanohito["dlDir"], ret['seriesName'])

		if not os.path.exists(ret["dirPath"]):
			os.makedirs(ret["dirPath"])

		self.log.info("Folderpath: %s", ret["dirPath"])


		ret['dlPage'] = self.getDownloadPageUrl(soup, sourcePage)



		return ret

	def doDownload(self, linkDict):

		if linkDict:


			fCont, fName = self.wg.getFileAndName(linkDict['dlPage'] , addlHeaders={'Referer': linkDict["sourceUrl"]})

			# self.log.info(len(content))
			if linkDict['originName'] in fName:
				fileN = fName
			elif not fName:
				fileN = '%s.zip' % (linkDict['originName'], )
				fileN = fileN.replace('.zip .zip', '.zip')
			else:
				fileN = '%s - %s.zip' % (linkDict['originName'], fName)
				fileN = fileN.replace('.zip .zip', '.zip')

			fileN = nt.makeFilenameSafe(fileN)
			fileN = self.insertCountIfFilenameExists(fileN)

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



			self.updateDbEntry(linkDict["sourceUrl"], downloadPath=linkDict["dirPath"], fileName=fileN)

			# Deduper uses the path info for relinking, so we have to dedup the item after updating the downloadPath and fileN
			dedupState = processDownload.processDownload(linkDict["seriesName"], wholePath, pron=True)
			self.log.info( "Done")

			if dedupState:
				self.addTags(sourceUrl=linkDict["sourceUrl"], tags=dedupState)


			self.updateDbEntry(linkDict["sourceUrl"], dlState=2)
			self.conn.commit()


		else:

			self.updateDbEntry(linkDict["sourceUrl"], dlState=-1, downloadPath="ERROR", fileName="ERROR: FAILED")

			self.conn.commit()
			return False


	def getLink(self, link):

		try:
			self.updateDbEntry(link["sourceUrl"], dlState=1)
			linkInfo = self.getDownloadInfo(link)

			if linkInfo:
				self.doDownload(linkInfo)

				sleeptime = random.randint(10,60*15)
			else:
				self.log.warning("Could not find direct download link!")
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
