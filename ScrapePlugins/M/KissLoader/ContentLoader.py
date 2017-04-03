

import logSetup
import runStatus
if __name__ == "__main__":
	runStatus.preloadDicts = False


import webFunctions
import settings
import os
import os.path

import nameTools as nt

import time
import sys

import urllib.parse
import html.parser
import zipfile
import traceback
import bs4
import re
import json
import ScrapePlugins.RetreivalBase
from mimetypes import guess_extension
from concurrent.futures import ThreadPoolExecutor
import ScrapePlugins.ScrapeExceptions as ScrapeExceptions

import processDownload
import magic

import execjs

class ContentLoader(ScrapePlugins.RetreivalBase.RetreivalBase):



	loggerPath = "Main.Manga.Ki.Cl"
	pluginName = "Kiss Manga Content Retreiver"
	tableKey = "ki"
	dbName = settings.DATABASE_DB_NAME
	tableName = "MangaItems"

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	retreivalThreads = 3

	itemLimit = 200

	def check_recaptcha(self, pgurl, soup=None, markup=None):
		if markup:
			soup = webFunctions.as_soup(markup)
		if not soup:
			raise RuntimeError("You have to pass either the raw page markup, or a pre-parsed bs4 soup object!")

		capdiv = soup.find("div", class_='g-recaptcha')
		if not capdiv:
			if markup:
				return markup
			return soup

		raise ScrapeExceptions.LimitedException("Encountered ReCaptcha! Cannot circumvent!")

		self.log.warning("Found ReCaptcha div. Need to circumvent.")
		sitekey = capdiv['data-sitekey']

		# soup.find("")


		params = {
			'key'       : settings.captcha_solvers['2captcha']['api_key'],
			'method'    : 'userrecaptcha',
			'googlekey' : sitekey,
			'pageurl'   : pgurl,
			'json'      : 1,
		}

		# self.wg.getJson("https://2captcha.com/in.php", postData=params)

		# # here we post site key to 2captcha to get captcha ID (and we parse it here too)
		# captcha_id = s.post("?key={}&method=userrecaptcha&googlekey={}&pageurl={}".format(API_KEY, site_key, url), proxies=proxy).text.split('|')[1]

		# # then we parse gresponse from 2captcha response
		# recaptcha_answer = s.get("http://2captcha.com/res.php?key={}&action=get&id={}".format(API_KEY, captcha_id), proxies=proxy).text
		# print("solving ref captcha...")
		# while 'CAPCHA_NOT_READY' in recaptcha_answer:
		# 	sleep(5)
		# 	recaptcha_answer = s.get("http://2captcha.com/res.php?key={}&action=get&id={}".format(API_KEY, captcha_id), proxies=proxy).text
		# recaptcha_answer = recaptcha_answer.split('|')[1]

		# # we make the payload for the post data here, use something like mitmproxy or fiddler to see what is needed
		# payload = {
		# 	'key': 'value',
		# 	'gresponse': recaptcha_answer  # This is the response from 2captcha, which is needed for the post request to go through.
		# 	}

		resolved = {
			"reUrl"                : "/Manga/Love-Lab-MIYAHARA-Ruri/Vol-010-Ch-001?id=359632",
			"g-recaptcha-response" : "03AOP2lf5kLccgf5aAkMmzXR8mN6Kv6s76BoqHIv-raSzGCa98HMPMdx0n04ourhM1mBApnesMRbzr2vFa0264mY83SCkL5slCFcC-i3uWJoHIjVhGh0GN4yyswg5-yZpDg1iK882nPuxEeaxb18pOK790x4Z18ib5UOPGU-NoECVb6LS03S3b4fCjWwRDLNF43WhkHDFd7k-Os7ULCgOZe_7kcF9xbKkovCh2uuK0ytD7rhiKnZUUvl1TimGsSaFkSSrQ1C4cxZchVXrz7kIx0r6Qp2hPr2_PW0CAutCkmr9lt9TS5n0ecdVFhdVQBniSB-NZv9QEpbQ8",
		}
		# # then send the post request to the url
		# response = s.post(url, payload, proxies=proxy)


	def getImage(self, imageUrl, referrer):

		content, handle = self.wg.getpage(imageUrl, returnMultiple=True, addlHeaders={'Referer': referrer})
		if not content or not handle:
			raise ValueError("Failed to retreive image from page '%s'!" % referrer)

		fileN = urllib.parse.unquote(urllib.parse.urlparse(handle.geturl())[2].split("/")[-1])
		fileN = bs4.UnicodeDammit(fileN).unicode_markup
		self.log.info("retreived image '%s' with a size of %0.3f K", fileN, len(content)/1000.0)

		if not "." in fileN:
			info = handle.info()
			if 'Content-Type' in info:
				tp = info['Content-Type']
				if ";" in tp:
					tp = tp.split(";")[0]
				ext = guess_extension(tp)
				if ext == None:
					ext = "unknown_ftype"
				print(info['Content-Type'], ext)
				fileN += "." + ext
			else:
				fileN += ".jpg"

		# Let magic figure out the files for us (it's probably smarter then kissmanga, anyways.)
		guessed = magic.from_buffer(content, mime=True)
		ext = guess_extension(tp)
		if ext:
			fileN = fileN + ext

		return fileN, content



	def getImageUrls(self, baseUrl):

		pgctnt, filename, mimetype = self.wg.getItemPhantomJS(baseUrl)

		pgctnt = self.check_recaptcha(pgurl=baseUrl, markup=pgctnt)

		linkRe = re.compile(r'lstImages\.push\((wrapKA\(".+?"\))\);')

		links = linkRe.findall(pgctnt)


		pages = []
		for item in links:
			tgt = self.wg.pjs_driver.execute_script("return %s" % item)
			if not tgt.startswith("http"):
				raise ScrapeExceptions.LimitedException("URL Decryption failed!")
			pages.append(tgt)

		self.log.info("Found %s pages", len(pages))


		return pages

	# Don't download items for 12 hours after relase,
	# so that other, (better) sources can potentially host
	# the items first.
	def checkDelay(self, inTime):
		return inTime < (time.time() - 60*60*12)



	def getLink(self, link):


		sourceUrl  = link["sourceUrl"]
		print("Link", link)



		seriesName = link['seriesName']


		try:
			self.log.info( "Should retreive url - %s", sourceUrl)
			self.updateDbEntry(sourceUrl, dlState=1)

			imageUrls = self.getImageUrls(sourceUrl)
			if not imageUrls:
				self.log.critical("Failure on retreiving content at %s", sourceUrl)
				self.log.critical("Page not found - 404")
				self.updateDbEntry(sourceUrl, dlState=-1)
				return



			self.log.info("Downloading = '%s', '%s' ('%s images)", seriesName, link["originName"], len(imageUrls))
			dlPath, newDir = self.locateOrCreateDirectoryForSeries(seriesName)

			if link["flags"] == None:
				link["flags"] = ""

			if newDir:
				self.updateDbEntry(sourceUrl, flags=" ".join([link["flags"], "haddir"]))

			chapterName = nt.makeFilenameSafe(link["originName"])

			fqFName = os.path.join(dlPath, chapterName+" [KissManga].zip")

			loop = 1
			prefix, ext = os.path.splitext(fqFName)
			while os.path.exists(fqFName):
				fqFName = "%s (%d)%s" % (prefix, loop,  ext)
				loop += 1
			self.log.info("Saving to archive = %s", fqFName)

			images = []
			imgCnt = 1
			for imgUrl in imageUrls:
				imageName, imageContent = self.getImage(imgUrl, sourceUrl)
				imageName = "{num:03.0f} - {srcName}".format(num=imgCnt, srcName=imageName)
				imgCnt += 1
				images.append([imageName, imageContent])

				if not runStatus.run:
					self.log.info( "Breaking due to exit flag being set")
					self.updateDbEntry(sourceUrl, dlState=0)
					return

			self.log.info("Creating archive with %s images", len(images))

			if not images:
				self.updateDbEntry(sourceUrl, dlState=-1, tags="error-404")
				return

			#Write all downloaded files to the archive.
			arch = zipfile.ZipFile(fqFName, "w")
			for imageName, imageContent in images:
				arch.writestr(imageName, imageContent)
			arch.close()


			dedupState = processDownload.processDownload(seriesName, fqFName, deleteDups=True, includePHash=True)
			self.log.info( "Done")

			filePath, fileName = os.path.split(fqFName)
			self.updateDbEntry(sourceUrl, dlState=2, downloadPath=filePath, fileName=fileName, tags=dedupState)
			return

		except SystemExit:
			print("SystemExit!")
			raise

		except Exception:
			self.log.critical("Failure on retreiving content at %s", sourceUrl)
			self.log.critical("Traceback = %s", traceback.format_exc())
			self.updateDbEntry(sourceUrl, dlState=-1)



	def setup(self):
		'''
		poke through cloudflare
		'''
		if not self.wg.stepThroughCloudFlare("http://kissmanga.com", 'KissManga'):
			raise ValueError("Could not access site due to cloudflare protection.")


if __name__ == '__main__':
	import utilities.testBase as tb

	with tb.testSetup(load=False):
		cl = ContentLoader()

		# pg = 'http://dynasty-scans.com/chapters/qualia_the_purple_ch16'
		# inMarkup = cl.wg.getpage(pg)
		# cl.getImageUrls(inMarkup, pg)
		cl.do_fetch_content()
		# cl.getLink('http://www.webtoons.com/viewer?titleNo=281&episodeNo=3')
		# cl.getImageUrls('http://kissmanga.com/Manga/Hanza-Sky/Ch-031-Read-Online?id=225102')


