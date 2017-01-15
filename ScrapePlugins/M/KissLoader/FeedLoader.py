
import runStatus
runStatus.preloadDicts = False


import webFunctions

import urllib.parse
import time
import calendar
import dateutil.parser
import settings
import urllib.error
import ScrapePlugins.RetreivalDbBase

# Only downlad items in language specified.
# Set to None to disable filtering (e.g. fetch ALL THE FILES).
DOWNLOAD_ONLY_LANGUAGE = "English"

class FeedLoader(ScrapePlugins.RetreivalDbBase.ScraperDbBase):



	loggerPath = "Main.Manga.Ki.Fl"
	pluginName = "Kiss Manga Link Retreiver"
	tableKey = "ki"
	dbName = settings.DATABASE_DB_NAME

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	tableName = "MangaItems"

	urlBase    = "http://kissmanga.com/"
	seriesBase = "http://kissmanga.com/MangaList/LatestUpdate?page={num}"


	def closeDB(self):
		self.log.info( "Closing DB...",)
		self.conn.close()
		self.log.info( "done")






	def getUpdatedSeries(self, url):
		ret = set()

		# This is probably a bit brittle. What the hell.
		end = \
'''<script type="text/javascript" src="../../Scripts/jqueryTooltip.js"></script>
Not found
<script type="text/javascript">'''
		if end in ret:
			return ret

		soup = self.wg.getSoup(url)

		if soup.find("table", class_='listing'):
			mainDiv = soup.find("table", class_='listing')
		else:
			raise ValueError("Could not find listing table?")




		for child in mainDiv.find_all("tr"):
			tds = child.find_all("td")
			if len(tds) != 2:
				# Table header - skip it
				continue

			series, dummy_release = tds

			seriesUrl = urllib.parse.urljoin(self.urlBase, series.a['href'])
			ret.add(seriesUrl)



		self.log.info("Found %s series", len(ret))

		return ret


	def getUpdatedSeriesPages(self, historical=False):

		# for item in items:
		# 	self.log.info( item)
		#

		self.log.info( "Loading KissManga Items")

		ret = []
		cnt = 1
		while 1:


			try:
				pages = self.getUpdatedSeries(self.seriesBase.format(num=cnt))
			except ValueError:
				break


			if not pages:
				break

			for page in pages:
				ret.append(page)

			if not runStatus.run:
				self.log.info( "Breaking due to exit flag being set")
				break

			if not historical:
				break
			else:
				if cnt > 100:
					break

			cnt += 1

		self.log.info("Found %s total items", len(ret))
		return ret

	# Check retreived page to see if it has a mature content warning
	# Step through if it does.
	# Returns page with actual content, either way
	def checkAdult(self, soup):
		adultPassThrough = soup.find("a", id='aYes')
		if not adultPassThrough:
			return soup

		self.log.info("Adult pass-through page. Stepping through")
		confirmLink = adultPassThrough['href']
		return self.wg.getSoup(confirmLink)


	def getSeriesInfoFromSoup(self, soup):
		# Should probably extract tagging info here. Laaaaazy
		# MangaUpdates interface does a better job anyways.

		titleA = soup.find("a", class_='bigChar')
		return {"seriesName": titleA.get_text()}

	def getChaptersFromSeriesPage(self, soup, historical=False):
		table = soup.find('table', class_='listing')

		items = []
		for row in table.find_all("tr"):
			if not row.a:
				continue  # Skip the table header row

			chapter, date = row.find_all("td")
			item = {}
			item["originName"] = chapter.get_text().strip()
			item["sourceUrl"]  = urllib.parse.urljoin(self.urlBase, chapter.a['href'])
			itemDate = dateutil.parser.parse(date.get_text().strip())
			item['retreivalTime'] = calendar.timegm(itemDate.timetuple())

			items.append(item)

		ret = []

		if not historical:
			maxDate = max([item["retreivalTime"] for item in items])
			for item in items:
				if item["retreivalTime"] == maxDate:
					ret.append(item)
		else:
			ret = items

		return ret

	def getChapterLinkFromSeriesPage(self, seriesUrl, historical=False):
		ret = []

		if " " in seriesUrl:
			seriesUrl = seriesUrl.replace(" ", "%20")
		soup = self.wg.getSoup(seriesUrl)
		soup = self.checkAdult(soup)

		seriesInfo = self.getSeriesInfoFromSoup(soup)

		chapters = self.getChaptersFromSeriesPage(soup, historical)
		for chapter in chapters:

			for key, val in seriesInfo.items(): # Copy series info into each chapter
				chapter[key] = val

			ret.append(chapter)

		self.log.info("Found %s items on page for series '%s'", len(ret), seriesInfo['seriesName'])

		return ret

	def getAllItems(self, historical=False):
		toScan = self.getUpdatedSeriesPages(historical)

		ret = []

		for url in toScan:
			try:
				items = self.getChapterLinkFromSeriesPage(url, historical)
				for item in items:
					if item in ret:
						self.log.warn("Duplicate items in ret?")
						# raise ValueError("Duplicate items in ret?")
					else:
						ret.append(item)
			except urllib.error.URLError:
				pass

		return ret


	def go(self, historical=False):


		if not self.wg.stepThroughCloudFlare("http://kissmanga.com/", titleContains='Read manga online in high quality'):
			raise ValueError("Could not access site due to cloudflare protection.")

		self.resetStuckItems()
		self.log.info("Getting feed items")

		feedItems = self.getAllItems(historical=historical)
		self.log.info("Processing feed Items")

		self.processLinksIntoDB(feedItems)
		self.log.info("Complete")


if __name__ == '__main__':
	import utilities.testBase as tb

	with tb.testSetup(startObservers=False):
		fl = FeedLoader()
		fl.go(historical=True)
		# fl.go(historical=True)
		# fl.getSeriesUrls()

		# fl.getAllItems()

