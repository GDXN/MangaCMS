



import webFunctions

import urllib.parse
import time
import calendar
import dateutil.parser
import runStatus
import settings
import os.path
import processDownload

import ScrapePlugins.RetreivalBase
import nameTools as nt

class Loader(ScrapePlugins.RetreivalBase.RetreivalBase):



	loggerPath = "Main.Manga.Yo.Fl"
	pluginName = "YoManga Scans Link Retreiver"
	tableKey = "ym"
	dbName = settings.DATABASE_DB_NAME

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	tableName = "MangaItems"

	urlBase    = "http://yomanga.co/"
	seriesBase = "http://yomanga.co/reader/directory/%s/"



	def doDownload(self, seriesName, dlurl, chapter_name):


		row = self.getRowsByValue(sourceUrl=dlurl, limitByKey=False)
		if row and row[0]['dlState'] != 0:
			return

		if not row:
			self.insertIntoDb(retreivalTime = time.time(),
								sourceUrl   = dlurl,
								originName  = seriesName,
								dlState     = 1,
								seriesName  = seriesName)


		fctnt, fname = self.wg.getFileAndName(dlurl)


		fileN = '{series} - {chap} [YoManga].zip'.format(series=seriesName, chap=chapter_name)
		fileN = nt.makeFilenameSafe(fileN)

		dlPath, newDir = self.locateOrCreateDirectoryForSeries(seriesName)
		wholePath = os.path.join(dlPath, fileN)

		self.log.info("Source name: %s", fname)
		self.log.info("Generated name: %s", fileN)

		if newDir:
			self.updateDbEntry(dlurl, flags="haddir")

		with open(wholePath, "wb") as fp:
			fp.write(fctnt)

		self.log.info("Successfully Saved to path: %s", wholePath)


		dedupState = processDownload.processDownload(seriesName, wholePath, deleteDups=True)
		if dedupState:
			self.addTags(sourceUrl=dlurl, tags=dedupState)

		self.updateDbEntry(dlurl, dlState=2, downloadPath=dlPath, fileName=fileN, originName=fileN)




	def getLink(self, url):
		new = 0
		total = 0


		soup = self.wg.getSoup(url)

		stitle = soup.find("h1", class_='title').get_text().strip()


		chapters = soup.find_all("div", class_='element')
		for chapter in chapters:
			dlurl = chapter.find("div", class_='fleft')
			chp_name = chapter.find("div", class_="title").get_text().strip()
			wasnew = self.doDownload(stitle, dlurl.a['href'], chp_name)
			if wasnew:
				new += 1
			total += 1


		return new, total

	def getSeriesUrls(self):
		ret = set()

		self.wg.stepThroughCloudFlare(self.seriesBase % 1, titleContains='Series List')

		page = 1
		while True:
			soup = self.wg.getSoup(self.seriesBase % page)

			new = False

			rows = soup.find_all('div', class_='group')

			for row in rows:
				if row.a['href'] not in ret:
					new = True
					ret.add(row.a['href'])

			page += 1
			if not new:
				break

		self.log.info("Found %s series", len(ret))

		return ret


	def go(self):
		self.log.info( "Loading YoManga Items")


		seriesPages = self.getSeriesUrls()

		tot_new, total_overall = 0, 0

		for item in seriesPages:

			new, total     = self.getLink(item)
			tot_new       += new
			total_overall += total

		self.log.info("Found %s total items, %s of which were new", total_overall, tot_new)
		return []



if __name__ == '__main__':

	# import logSetup
	# logSetup.initLogging()
	# fl = Loader()
	# print("fl", fl)
	# fl.go()

	# urls = fl.getContentForItem('http://yomanga.co/reader/series/brawling_go/')
	# urls = fl.getSeriesUrls()
	# print(urls)


	import utilities.testBase as tb
	with tb.testSetup():

		fl = Loader()
		print("fl", fl)
		fl.go()
		# fl = Loader()
		# print("fl", fl)
		# # fl.go()
		# fl.getSeriesUrls()
		# items = fl.getItemPages('http://mangastream.com/manga/area_d')
		# print("Items")
		# for item in items:
		# 	print("	", item)

