



import webFunctions

import urllib.parse
import time
import calendar
import dateutil.parser
import runStatus
import settings
import os.path
import processDownload

import ScrapePlugins.RetreivalDbBase
import nameTools as nt

class Loader(ScrapePlugins.RetreivalDbBase.ScraperDbBase):



	loggerPath = "Main.Manga.Yo.Fl"
	pluginName = "YoManga Scans Link Retreiver"
	tableKey = "ym"
	dbName = settings.DATABASE_DB_NAME

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	tableName = "MangaItems"

	urlBase    = "http://yomanga.co/"
	seriesBase = "http://yomanga.co/reader/directory"


	def closeDB(self):
		self.log.info( "Closing DB...",)
		self.conn.close()
		self.log.info( "done")





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
			self.conn.commit()

		with open(wholePath, "wb") as fp:
			fp.write(fctnt)

		self.log.info("Successfully Saved to path: %s", wholePath)


		dedupState = processDownload.processDownload(seriesName, wholePath, deleteDups=True)
		if dedupState:
			self.addTags(sourceUrl=dlurl, tags=dedupState)

		self.updateDbEntry(dlurl, dlState=2, downloadPath=dlPath, fileName=fileN, originName=fileN)

		self.conn.commit()



	def getContentForItem(self, url):
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

		soup = self.wg.getSoup(self.seriesBase)

		rows = soup.find_all('div', class_='group')

		for row in rows:
			ret.add(row.a['href'])

		self.log.info("Found %s series", len(ret))

		return ret


	def getAllItems(self):
		self.log.info( "Loading YoManga Items")


		seriesPages = self.getSeriesUrls()

		tot_new, total_overall = 0, 0

		for item in seriesPages:

			new, total     = self.getContentForItem(item)
			tot_new       += new
			total_overall += total

		self.log.info("Found %s total items, %s of which were new", total_overall, tot_new)
		return []


	def go(self):

		self.resetStuckItems()
		self.log.info("Getting feed items")

		feedItems = self.getAllItems()
		self.log.info("Processing feed Items")

		self.processLinksIntoDB(feedItems)
		self.log.info("Complete")


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
	with tb.testSetup(startObservers=False):

		fl = Loader()
		print("fl", fl)
		fl.go()
	# 	fl = Loader()
	# 	print("fl", fl)
	# 	# fl.go()
	# 	fl.getSeriesUrls()
		# items = fl.getItemPages('http://mangastream.com/manga/area_d')
		# print("Items")
		# for item in items:
		# 	print("	", item)

