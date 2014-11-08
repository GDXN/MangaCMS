
import webFunctions

import settings
import nameTools as nt
import time

import ScrapePlugins.RetreivalDbBase


class FeedLoader(ScrapePlugins.RetreivalDbBase.ScraperDbBase):


	dbName = settings.dbName
	loggerPath = "Main.TwistedHel.Fl"
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




if __name__ == "__main__":
	import utilities.testBase as tb

	with tb.testSetup(startObservers=False):
		# getHistory()
		run = FeedLoader()
		# ret = run.getFeed()
		# for row in ret:
		# 	print(row)
		# print("Total items = ", len(ret))

		# run.getSeriesPages()
		# run.getChaptersFromSeriesPage('http://www.twistedhelscans.com/series/trace_20/')  # Licensed, no returns
		# run.getChaptersFromSeriesPage('http://www.twistedhelscans.com/series/god_eater_the_2nd_break/')

		run.go()


