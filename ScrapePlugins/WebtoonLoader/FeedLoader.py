

import logSetup
import runStatus
if __name__ == "__main__":
	logSetup.initLogging()
	runStatus.preloadDicts = False


import webFunctions

import urllib.parse
import time
import calendar
import dateutil.parser
import runStatus
import settings
import datetime

import ScrapePlugins.RetreivalDbBase
import nameTools as nt

# Only downlad items in language specified.
# Set to None to disable filtering (e.g. fetch ALL THE FILES).
DOWNLOAD_ONLY_LANGUAGE = "English"

class FeedLoader(ScrapePlugins.RetreivalDbBase.ScraperDbBase):



	loggerPath = "Main.Manga.Wt.Fl"
	pluginName = "Webtoons.com Scans Link Retreiver"
	tableKey = "wt"
	dbName = settings.DATABASE_DB_NAME

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	tableName = "MangaItems"

	urlBase    = "http://www.webtoons.com/"
	seriesBase = "http://www.webtoons.com/genre"


	def closeDB(self):
		self.log.info( "Closing DB...",)
		self.conn.close()
		self.log.info( "done")




	def extractItemInfo(self, soup):

		ret = {}

		titleH = soup.find("h1", class_='subj')
		# print(titleH)
		titleH.div.decompose()
		# titleDiv = soup.find("h1", class_="ttl")
		ret["title"] = titleH.get_text().strip()

		return ret

	def getItemPages(self, pageUrl, historical=False):
		self.log.info("Should get item for '%s'", pageUrl)


		urlFormat = '%s&page={num}' % pageUrl

		pageNo = 1

		ret = []
		while 1:

			soup = self.wg.getSoup(urlFormat.format(num=pageNo))
			baseInfo = self.extractItemInfo(soup)

			listDiv = soup.find_all("div", class_="detail_lst")
			if len(listDiv) != 1:
				raise ValueError("Found incorrect number of detail list div items! %s" % len(listDiv))
			listDiv = listDiv[0]

			hadNew = False

			for listItem in listDiv.find_all("li"):

				if not listItem.a:
					continue

				chapSpan = listItem.find("span", class_='subj')

				if chapSpan.em:
					chapSpan.em.decompose()

				chapTitle = chapSpan.get_text().strip()

				# Fix stupid chapter naming
				chapTitle = chapTitle.replace("Ep. ", "c")

				dateSpan = listItem.find("span", class_='date')
				date = dateutil.parser.parse(dateSpan.get_text().strip(), fuzzy=True)

				item = {}

				url = listItem.a["href"]
				url = urllib.parse.urljoin(self.urlBase, url)



				item["originName"]    = "{series} - {file}".format(series=baseInfo["title"], file=chapTitle)
				item["sourceUrl"]     = url
				item["seriesName"]    = baseInfo["title"]
				item["retreivalTime"] = calendar.timegm(date.timetuple())

				if not item in ret:
					hadNew = True
					ret.append(item)


			if not historical:
				break
			if not hadNew:
				break

			pageNo += 1


		self.log.info("Found %s chapters for series '%s'", len(ret), baseInfo["title"])
		return ret



	def getSeriesUrls(self):
		ret = set()

		soup = self.wg.getSoup(self.seriesBase)
		lists = soup.find_all("ul", class_='card_lst')


		for subList in lists:
			for series in subList.find_all("li"):
				val = series.a['href']

				# Fix broken source URLs.
				val = val.replace(" ", "%20")

				url = urllib.parse.urljoin(self.urlBase, val)
				ret.add(url)
			# if td.a:
			# 	link = td.a["href"]
			# 	if self.urlBase in link:
			# 		ret.append(link)

		self.log.info("Found %s series", len(ret))

		return ret


	def getAllItems(self, historical=False):
		# for item in items:
		# 	self.log.info( item)
		#

		self.log.info( "Loading Red Hawk Items")

		ret = []

		seriesPages = self.getSeriesUrls()


		for item in seriesPages:

			itemList = self.getItemPages(item, historical=historical)
			for item in itemList:
				ret.append(item)

			if not runStatus.run:
				self.log.info( "Breaking due to exit flag being set")
				break
		self.log.info("Found %s total items", len(ret))
		return ret


	def go(self, historical=False):

		self.resetStuckItems()
		self.log.info("Getting feed items")

		feedItems = self.getAllItems(historical=historical)
		self.log.info("Processing feed Items")

		self.processLinksIntoDB(feedItems)
		self.log.info("Complete")


if __name__ == '__main__':
	fl = FeedLoader()
	print("fl", fl)
	# fl.go(historical=True)
	fl.go()
	# fl.getSeriesUrls()
	# items = fl.getItemPages('http://www.webtoons.com/episodeList?titleNo=78')
	# print("Items")
	# for item in items:
	# 	print("	", item)

