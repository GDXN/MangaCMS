

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



	loggerPath = "Main.Manga.Dy.Fl"
	pluginName = "Dynasty Scans Link Retreiver"
	tableKey = "dy"
	dbName = settings.DATABASE_DB_NAME

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	tableName = "MangaItems"

	urlBase    = "http://dynasty-scans.com/"
	seriesBase = "http://dynasty-scans.com/?page={num}"


	def closeDB(self):
		self.log.info( "Closing DB...",)
		self.conn.close()
		self.log.info( "done")




	def extractItemInfo(self, soup):

		ret = {}

		titleH = soup.find("h3", class_='subj')

		# titleDiv = soup.find("h1", class_="ttl")
		ret["title"] = titleH.get_text().strip()

		return ret


	def getItems(self, url):
		ret = []

		soup = self.wg.getSoup(url)

		if soup.find("div", class_='span8'):
			mainDiv = soup.find("div", class_='span8')
		elif soup.find("div", class_='chapters index'):
			mainDiv = soup.find("div", class_='chapters index')
		else:
			raise ValueError("Could not find item container?")



		curDate = None
		for child in mainDiv.find_all(True, recursive=False):  # Iterate over only tag children

			if child.name == 'h4':
				curDate = dateutil.parser.parse(child.string.strip())
			elif child.name == 'a':

				item = {}

				item["sourceUrl"] = urllib.parse.urljoin(self.urlBase, child['href'])
				item["retreivalTime"] = calendar.timegm(curDate.timetuple())

				titleDiv = child.find("div", class_='title')

				title = titleDiv.contents[0].strip()
				if titleDiv.small:
					title += ' {%s}' % titleDiv.small.text.strip()

				item["originName"] = title

				tagDiv = child.find('div', class_='tags')
				if tagDiv:
					tags = tagDiv.find_all("span")
					tags = [tag.get_text().replace(" ", "-").replace(":", "").lower() for tag in tags]
					tags = ' '.join(tags)
					item["tags"] = tags


				ret.append(item)

			else:
				# Pagination stuff, etc...
				continue


		self.log.info("Found %s series", len(ret))

		return ret


	def getAllItems(self, historical=False):
		# for item in items:
		# 	self.log.info( item)
		#

		self.log.info( "Loading Dynasty Scans Items")

		ret = []
		cnt = 1
		while 1:



			pages = self.getItems(self.seriesBase.format(num=cnt))


			if not pages:
				break

			for page in pages:
				ret.append(page)

			if not runStatus.run:
				self.log.info( "Breaking due to exit flag being set")
				break

			if not historical:
				break

			cnt += 1

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
	fl.go(historical=True)
	# fl.getSeriesUrls()
	# fl.getAllItems()
	# items = fl.getItemPages('http://www.webtoons.com/episodeList?titleNo=78')
	# print("Items")
	# for item in items:
	# 	print("	", item)

