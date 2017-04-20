
# -*- coding: utf-8 -*-

import webFunctions
import os
import os.path

import zipfile
import nameTools as nt

import urllib.request, urllib.parse, urllib.error
import traceback

import settings
import json
import processDownload

import ScrapePlugins.RetreivalBase

class ContentLoader(ScrapePlugins.RetreivalBase.RetreivalBase):



	dbName = settings.DATABASE_DB_NAME
	loggerPath = "Main.Manga.CrunchyRoll.Cl"
	pluginName = "CrunchyRoll Content Retreiver"
	tableKey   = "cr"
	urlBase    = "http://www.crunchyroll.com/"

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	tableName = "MangaItems"

	retreivalThreads = 1



	def getChapterId(self, apiServer, seriesId, wantChapNum):
		# >>> urllib.parse.urlsplit('http://api-manga.crunchyroll.com/list_chapters?series%5Fid=181&user%5Fid=null')
		# SplitResult(scheme='http', netloc='api-manga.crunchyroll.com', path='/list_chapters', query='series%5Fid=181&user%5Fid=null', fragment='')
		query = {"series_id": seriesId, "user_id": 'null'}
		query = urllib.parse.urlencode(query)

		# Crunchyroll seems to be (unnecessarily) urlescaping the underscores in the query parameters of
		# their AJAX request urls. Mimic that behaviour
		query = query.replace("_", '%5F')

		params = ("http", apiServer, '/list_chapters', '', query, '')
		url = urllib.parse.urlunparse(params)

		seriesInfo = self.wg.getpage(url)
		if not seriesInfo:
			return []

		seriesInfo = json.loads(seriesInfo)

		ret = None
		for chapter in seriesInfo['chapters']:
			if chapter['viewable']:
				if not "locale" in chapter:
					continue
				if not 'enUS' in chapter["locale"]:
					continue
				if not 'name' in chapter["locale"]['enUS']:
					continue

				if chapter['number'] == wantChapNum:

					ret = (chapter['chapter_id'], chapter["locale"]['enUS']['name'])
		return ret

	def getChapterData(self, apiServer, chapterId, sessionId):
		# http://api-manga.crunchyroll.com/list_chapter?chapter%5Fid=6507&auth=null&session%5Fid=4q5akot51gbglzior4wxdjdqbxzhkwgd

		# >>> urllib.parse.urlsplit('http://api-manga.crunchyroll.com/list_chapters?series%5Fid=181&user%5Fid=null')
		# SplitResult(scheme='http', netloc='api-manga.crunchyroll.com', path='/list_chapters', query='series%5Fid=181&user%5Fid=null', fragment='')
		query = {"chapter_id": chapterId, "session_id": sessionId, "user_id": 'null', "auth": 'null'}
		query = urllib.parse.urlencode(query)

		# Crunchyroll seems to be (unnecessarily) urlescaping the underscores in the query parameters of
		# their AJAX request urls. Mimic that behaviour
		query = query.replace("_", '%5F')

		params = ("http", apiServer, '/list_chapter', '', query, '')
		url = urllib.parse.urlunparse(params)

		chapterInfo = self.wg.getpage(url)
		if not chapterInfo:
			return []

		chapterInfo = json.loads(chapterInfo)


		imageUrls = []

		# so there is a field in the json data named 'page_number'. However,
		# it seems to be almost always set to 0. Yeeeeeah.....
		# Theres a lot of other shit in the JSON as well. There are
		# cleaned pages (no typsetting), polygon extents (for client-side typesetting?)
		# etc...
		pageno = 1
		for page in chapterInfo['pages']:
			print(page)
			if 'locale' in page and page['locale'] and 'enUS' in page['locale'] and page['locale']['enUS']:
				if 'encrypted_composed_image_url' in page['locale']['enUS']:
					url = page['locale']['enUS']['encrypted_composed_image_url']
					if url == None or url == 'null':
						raise ValueError("Item has null URLs?")
					imageUrls.append((pageno, url))

					pageno += 1

		return imageUrls

	def fetchImageUrls(self, soup):

		flashConf = soup.find('param', attrs={'name':'flashvars'})
		if not flashConf:
			return False
		conf = dict(urllib.parse.parse_qsl(flashConf['value']))

		apiServer = conf['server']
		chapInfo = self.getChapterId(apiServer, conf['seriesId'], conf['chapterNumber'])
		if not chapInfo:
			return False

		chapterId, chapterName = chapInfo

		chapImages = self.getChapterData(apiServer, chapterId, conf['session_id'])

		ret = []
		for imNum, url in chapImages:
			# AFICT, they /only/ use jpeg.
			# Realistically, I don't care (all internal stuff autodetects),
			# but it'd be nice to have the correct extensions. Assume jpeg for the moment.
			fname = 'img {num:05d}.jpeg'.format(num=imNum)
			ret.append((fname, url))


		return ret, chapterName, conf['chapterNumber']



	def getDownloadInfo(self, linkDict, retag=False):
		sourcePage = linkDict["sourceUrl"]

		self.log.info("Retreiving item: %s", sourcePage)

		try:
			soup = self.wg.getSoup(sourcePage, addlHeaders={'Referer': self.urlBase})
		except:
			self.log.critical("No download at url %s! SourceUrl = %s", sourcePage, linkDict["sourceUrl"])
			raise IOError("Invalid webpage")


		dlPath, newDir = self.locateOrCreateDirectoryForSeries(linkDict['seriesName'])
		linkDict['dirPath'] = dlPath

		if newDir:
			if not linkDict["flags"]:
				linkDict["flags"] = ''
			self.updateDbEntry(sourcePage, flags=" ".join([linkDict["flags"], "haddir"]))

		if not os.path.exists(linkDict["dirPath"]):
			os.makedirs(linkDict["dirPath"])
		else:
			self.log.info("Folder Path already exists?: %s", linkDict["dirPath"])


		self.log.info("Folderpath: %s", linkDict["dirPath"])
		#self.log.info(os.path.join())

		urls = self.fetchImageUrls(soup)
		if not urls:
			self.log.warn("No urls in chapter metadata?")
			return False

		imageUrls, linkDict["originName"], linkDict["chapterNo"] = urls


		linkDict["dlLinks"] = imageUrls

		self.log.info("Found %s images in manga.", len(imageUrls))

		self.log.debug("Linkdict = ")
		for key, value in list(linkDict.items()):
			self.log.debug("		%s - %s", key, value)


		return linkDict



	def getImage(self, imageUrl):
		# the image URL format seems to be '{hash of some sort}_{creation timestamp}_main'
		# I checked a few common hash algos, the hash is not a pre/post decryption md5, nor sha1

		content = self.wg.getpage(imageUrl, addlHeaders={'Referer': ' http://www.crunchyroll.com/swf/MangaViewer.swf?1'})
		if not content:
			raise ValueError("Failed to retreive image from page '%s'!" % imageUrl)

		self.log.info("retreived file with a size of %0.3f K", len(content)/1000.0)

		# "decrypt" the file. By XORing with 0x42.
		# Yeeeeeah. "Security"
		content = bytearray(content)
		for x in range(len(content)):
			content[x] = content[x] ^ 0x42
		content = bytes(content)

		return content



	def fetchImages(self, linkDict):

		images = []
		for filename, imgUrl in linkDict["dlLinks"]:
			images.append((filename, self.getImage(imgUrl)))

		return images



	def doDownload(self, linkDict, link, retag=False):

		images = self.fetchImages(linkDict)
		# images = ['wat']
		# print(linkDict)
		# self.log.info(len(content))

		if images:
			linkDict["chapterNo"] = float(linkDict["chapterNo"])
			fileN = '{series} - c{chapNo:06.1f} - {sourceName} [crunchyroll].zip'.format(series=linkDict['seriesName'], chapNo=linkDict["chapterNo"], sourceName=linkDict['originName'])
			fileN = nt.makeFilenameSafe(fileN)


			# self.log.info("geturl with processing", fileN)
			wholePath = os.path.join(linkDict["dirPath"], fileN)
			self.log.info("Complete filepath: %s", wholePath)

					#Write all downloaded files to the archive.
			arch = zipfile.ZipFile(wholePath, "w")
			for imageName, imageContent in images:
				arch.writestr(imageName, imageContent)
			arch.close()


			self.log.info("Successfully Saved to path: %s", wholePath)

			if not linkDict["tags"]:
				linkDict["tags"] = ""



			dedupState = processDownload.processDownload(linkDict["seriesName"], wholePath, deleteDups=True, rowId=link['dbId'])
			self.log.info( "Done")


			if dedupState:
				self.addTags(sourceUrl=linkDict["sourceUrl"], tags=dedupState)

			self.updateDbEntry(linkDict["sourceUrl"], dlState=2, downloadPath=linkDict["dirPath"], fileName=fileN, originName=fileN)
			return wholePath

		else:

			self.updateDbEntry(linkDict["sourceUrl"], dlState=-1, downloadPath="ERROR", fileName="ERROR: FAILED")
			return False


	def getLink(self, link):

		try:
			self.updateDbEntry(link["sourceUrl"], dlState=1)
			linkInfo = self.getDownloadInfo(link)
			if linkInfo:
				self.doDownload(linkInfo, link)
			else:
				print("No link info?")
				self.deleteRowsByValue(sourceUrl=link["sourceUrl"])

		except urllib.error.URLError:
			self.log.error("Failure retreiving content for link %s", link)
			self.log.error("Traceback: %s", traceback.format_exc())
		except IOError:
			self.log.error("Failure retreiving content for link %s", link)
			self.log.error("Traceback: %s", traceback.format_exc())
		except OSError:
			self.log.error("Failure retreiving content for link %s", link)
			self.log.error("Traceback: %s", traceback.format_exc())

		# 	self.updateDbEntry(link["sourceUrl"], dlState=-1, downloadPath="ERROR", fileName="ERROR: FAILED")


if __name__ == "__main__":
	import utilities.testBase as tb

	with tb.testSetup():

		run = ContentLoader()
		# ret = run.getLink(test)
		# run.getChapterId('api-manga.crunchyroll.com', '181', '238.00')
		# run.getChapterData('api-manga.crunchyroll.com', '6507', '4q5akot51gbglzior4wxdjdqbxzhkwgd')

		# run.getImage('http://img1.ak.crunchyroll.com/i/croll_manga/e/8a6bb34ab61cdac5b3039ac640d7a26b_1414594502_main')
		# run.resetStuckItems()
		run.go()
