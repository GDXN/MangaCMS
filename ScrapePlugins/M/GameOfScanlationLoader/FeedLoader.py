

import logSetup
import runStatus
if __name__ == "__main__":
	logSetup.initLogging()
	runStatus.preloadDicts = False


import webFunctions

import urllib.parse
import calendar
import dateutil.parser
import settings

import ScrapePlugins.RetreivalDbBase

class FeedLoader(ScrapePlugins.RetreivalDbBase.ScraperDbBase):



	loggerPath = "Main.Manga.GoS.Fl"
	pluginName = "Game of Scanlation Scans Link Retreiver"
	tableKey = "gos"
	dbName = settings.DATABASE_DB_NAME

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	tableName = "MangaItems"

	urlBase    = "https://gameofscanlation.moe/"
	seriesBase = "https://gameofscanlation.moe/projects/"


	def closeDB(self):
		self.log.info( "Closing DB...",)
		self.conn.close()
		self.log.info( "done")




	def extractItemInfo(self, soup):

		ret = {}
		header_banner = soup.find('div', class_='chapban')

		ret["title"] = header_banner.h2.get_text().strip()

		return ret

	def getItemPages(self, pageUrl):
		self.log.info("Should get item for '%s'", pageUrl)

		ret = []


		while True:

			soup = self.wg.getSoup(pageUrl)
			baseInfo = self.extractItemInfo(soup)
			chapters = soup.find('ol', class_='discussionListItems')

			had_new = False
			for row in chapters.find_all("li", class_='discussionListItem'):
				chp_p = row.find('p', class_='text_work')
				if not chp_p:
					continue
				if not chp_p.a:
					continue

				ulDate = row.find(True, class_='DateTime')

				chapTitle = chp_p.get_text().strip()

				# Fix stupid chapter naming
				chapTitle = chapTitle.replace("Ep. ", "c")


				if ulDate.has_attr("data-time"):
					timestamp = ulDate['data-time']
				elif ulDate.has_attr("title"):
					date = dateutil.parser.parse(ulDate['title'].strip(), fuzzy=True)
					timestamp = calendar.timegm(date.timetuple())
				else:
					raise ValueError("Wat?")

				item = {}

				url = row.a["href"]
				url = urllib.parse.urljoin(self.urlBase, url)

				item["originName"]    = "{series} - {file}".format(series=baseInfo["title"], file=chapTitle)
				item["sourceUrl"]     = url
				item["seriesName"]    = baseInfo["title"]
				item["retreivalTime"] = timestamp

				nav = soup.find('div', class_='PageNav')
				if nav:
					nextpg = nav.find("a", class_='text', text='Next >')
					if nextpg:
						pageUrl = urllib.parse.urljoin(self.urlBase, nextpg['href'])

				if not item in ret:
					had_new = True
					ret.append(item)
			if not had_new:
				break

		self.log.info("Found %s chapters for series '%s'", len(ret), baseInfo["title"])
		return ret



	def getSeriesUrls(self):
		ret = set()

		soup = self.wg.getSoup(self.seriesBase)
		cols = soup.find_all('section', class_='projectslisting')

		for col in cols:

			entries = col.find_all("div", class_="section")


			for entry in entries:
				infodiv = entry.find('div', class_='info')
				if not infodiv:
					continue

				if not infodiv.a:
					continue

				itemurl = urllib.parse.urljoin(self.urlBase, infodiv.a['href'])
				ret.add(itemurl)

		self.log.info("Found %s series", len(ret))

		return ret


	def getAllItems(self, historical=False):
		# for item in items:
		# 	self.log.info( item)
		#

		self.log.info( "Loading GameOfScanlation Items")

		ret = []

		seriesPages = self.getSeriesUrls()


		for item in seriesPages:

			itemList = self.getItemPages(item)
			for item in itemList:
				ret.append(item)

			if not runStatus.run:
				self.log.info( "Breaking due to exit flag being set")
				break
		self.log.info("Found %s total items", len(ret))
		return ret


	def go(self):

		self.resetStuckItems()
		self.log.info("Getting feed items")

		feedItems = self.getAllItems()
		self.log.info("Processing feed Items")

		self.processLinksIntoDB(feedItems)
		self.log.info("Complete")


if __name__ == '__main__':
	fl = FeedLoader()
	print("fl", fl)
	fl.go()
	# print(fl.getAllItems())
	# print(fl.getItemPages('https://gameofscanlation.moe/projects/hero-waltz/'))
	# print(fl.getItemPages('https://gameofscanlation.moe/projects/mujang/'))
	# print(fl.getItemPages('https://gameofscanlation.moe/projects/hclw/'))
	# print(fl.getItemPages('https://gameofscanlation.moe/projects/one-room-hero/'))
	# fl.getSeriesUrls()
	# items = fl.getItemPages('http://mangastream.com/manga/area_d')
	# print("Items")
	# for item in items:
	# 	print("	", item)

