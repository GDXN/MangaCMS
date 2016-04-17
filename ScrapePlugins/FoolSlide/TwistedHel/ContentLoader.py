
# -*- coding: utf-8 -*-

import webFunctions
import os
import os.path

import zipfile
import nameTools as nt

import urllib.request, urllib.parse, urllib.error


import settings
import bs4
import json
import re
import ScrapePlugins.RetreivalBase

import ScrapePlugins.FoolSlide.FoolSlideDownloadBase

class ContentLoader(ScrapePlugins.FoolSlide.FoolSlideDownloadBase.FoolContentLoader):

	dbName = settings.DATABASE_DB_NAME
	loggerPath = "Main.Manga.TwistedHel.Cl"
	pluginName = "TwistedHel Content Retreiver"
	tableKey    = "th"
	urlBase = "http://www.twistedhelscans.com/"

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	tableName = "MangaItems"

	retreivalThreads = 1

	groupName = 'TwistedHelScans'


	contentSelector = None


	def getImageUrls(self, baseUrl):

		pageCtnt = self.wg.getpage(baseUrl)

		if "The following content is intended for mature audiences" in pageCtnt:
			self.log.info("Adult check page. Confirming...")
			pageCtnt = self.wg.getpage(baseUrl, postData={"adult": "true"})


		if "The following content is intended for mature audiences" in pageCtnt:
			raise ValueError("Wat?")
		soup = bs4.BeautifulSoup(pageCtnt, "lxml")

		container = soup.find('body')

		if not container:
			raise ValueError("Unable to find javascript container div '%s'" % baseUrl)

		# If there is a ad div in the content container, it'll mess up the javascript match, so
		# find it, and remove it from the tree.
		container.find('div', class_='isreaderc').decompose()
		# if container.find('div', class_='ads'):
		# 	container.find('div', class_='ads').decompose()


		scriptText = container.script.get_text()

		if not scriptText:
			raise ValueError("No contents in script tag? '%s'" % baseUrl)


		jsonRe = re.compile(r'var pages = (\[.+?\]);', re.DOTALL)
		jsons = jsonRe.findall(scriptText)

		if not jsons:
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




if __name__ == "__main__":
	import utilities.testBase as tb

	with tb.testSetup(startObservers=False):

		run = ContentLoader()
		run.go()
