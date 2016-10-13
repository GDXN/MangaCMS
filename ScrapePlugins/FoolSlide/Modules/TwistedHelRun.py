

import bs4
import json
import nameTools as nt
import os
import os.path
import re
import runStatus
import ScrapePlugins.FoolSlide.FoolSlideDownloadBase
import ScrapePlugins.RetreivalBase
import ScrapePlugins.RetreivalDbBase
import ScrapePlugins.RunBase
import settings
import time
import urllib.request, urllib.parse, urllib.error
import webFunctions
import zipfile

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


		jsonRe = re.compile(r'var pages = (\[.*?\]);', re.DOTALL)
		jsons = jsonRe.findall(pageCtnt)

		if not jsons:
			raise ValueError("No JSON variable in script! '%s'" % baseUrl)

		data = jsons.pop()
		print(data)
		if data == "[]":
			arr = []
		else:
			arr = json.loads(data)

		imageUrls = []

		for item in arr:
			scheme, netloc, path, query, fragment = urllib.parse.urlsplit(item['url'])
			path = urllib.parse.quote(path)
			itemUrl = urllib.parse.urlunsplit((scheme, netloc, path, query, fragment))

			imageUrls.append((item['filename'], itemUrl, baseUrl))

		if not imageUrls:
			raise ValueError("Unable to find contained images on page '%s'" % baseUrl)


		return imageUrls



class FeedLoader(ScrapePlugins.RetreivalDbBase.ScraperDbBase):


	dbName = settings.DATABASE_DB_NAME
	loggerPath = "Main.Manga.TwistedHel.Fl"
	pluginName = "TwistedHel Link Retreiver"
	tableKey    = "th"
	urlBase = "http://www.twistedhelscans.com/"
	urlFeed = "http://www.twistedhelscans.com/directory/"

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	tableName = "MangaItems"



	def getChaptersFromSeriesPage(self, inUrl):

		soup = self.wg.getSoup(inUrl)

		if 'The following content is intended for mature' in soup.get_text():
			self.log.info("Adult check page. Confirming...")
			soup = self.wg.getSoup(inUrl, postData={"adult": "true"})

		mainDiv = soup.find('div', id='series_right')

		seriesName = mainDiv.h1.get_text()

		seriesName = nt.getCanonicalMangaUpdatesName(seriesName)

		# No idea why chapters are class 'staff_link'. Huh.
		chapters = mainDiv.find_all('div', class_='staff_link')


		ret = []
		for chapter in chapters:
			item = {}
			item['originName'] = "{series} - {file}".format(series=seriesName, file=chapter.a.get_text())
			item['sourceUrl']  = chapter.a['href']
			item['seriesName'] = seriesName
			item['retreivalTime'] = time.time()    # Fukkit, just use the current date.
			ret.append(item)
		return ret

	def getSeriesPages(self):
		soup = self.wg.getSoup(self.urlFeed)
		pageDivs = soup.find_all("div", class_='series_card')

		ret = []
		for div in pageDivs:

			ret.append(div.a['href'])

		return ret


	def getFeed(self):
		ret = []
		for seriesPage in self.getSeriesPages():
			for item in self.getChaptersFromSeriesPage(seriesPage):
				ret.append(item)

		return ret


	def go(self):
		self.resetStuckItems()
		dat = self.getFeed()


		self.processLinksIntoDB(dat)




class Runner(ScrapePlugins.RunBase.ScraperBase):


	loggerPath = "Main.Manga.TwistedHel.Run"
	pluginName = "TwistedHel"



	def _go(self):
		fl = FeedLoader()
		fl.go()
		fl.closeDB()


		if not runStatus.run:
			return

		cl = ContentLoader()
		cl.go()
		cl.closeDB()


if __name__ == "__main__":
	import utilities.testBase as tb

	with tb.testSetup():
		# run = Runner()
		# run.go()

		runStatus.run = True
		cl = ContentLoader()
		cl.go()
		cl.closeDB()

		# cl = ContentLoader()
		# pg = 'http://www.twistedhelscans.com/read/trace_15/en/0/33/page/1'
		# pg = 'http://www.twistedhelscans.com/read/trace_15/en/0/32/'
		# cl.getImageUrls(pg)