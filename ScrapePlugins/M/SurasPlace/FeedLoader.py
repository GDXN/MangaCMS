
import webFunctions
import bs4
import time
import urllib.parse
import runStatus
import settings
import ScrapePlugins.LoaderBase


class FeedLoader(ScrapePlugins.LoaderBase.LoaderBase):



	loggerPath = "Main.Manga.Sura.Fl"
	pluginName = "Sura's Place Link Retreiver"
	tableKey = "sura"
	dbName = settings.DATABASE_DB_NAME

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	tableName = "MangaItems"

	urlBase = "http://www.surasplace.com/"

	feedUrl = "http://www.surasplace.com/index.php/projects/popular/page{num}.html"


	def getSeriesPages(self):

		page = 1

		links = set()
		hadNew = True
		while (hadNew):
			hadNew = False
			url = self.feedUrl.format(num=page)
			soup = self.wg.getSoup(url)
			divs = soup.find_all("div", class_='lsrow')
			for div in divs:
				header = div.find("div", class_='header')
				if not header.find("span", itemprop='name'):
					continue

				itemUrl  = header.h3.a['href']
				itemName = header.h3.a.span.get_text()
				fullUrl = urllib.parse.urljoin(self.urlBase, itemUrl)

				# Apparently content is added manually, leading to some broken URLs.
				# anyways, fix those as they crop up.
				if fullUrl.endswith("htmll"):
					fullUrl = fullUrl[:-1]

				for x in range(len(fullUrl)):
					if fullUrl[x:] == fullUrl[:x]:
						fullUrl = fullUrl[x:]
						break

				if not fullUrl in links:
					links.add(fullUrl)
					hadNew |= True

			page += 1

		self.log.info("Found %s series-like items.", len(links))
		return links

	def extractItemInfo(self, soup):

		ret = {}

		titleDiv = soup.find("span", itemprop="name")
		ret["title"] = titleDiv.get_text()

		# Holy shit, unique IDs for each metadata field. Halle-fucking-lujah
		tags = soup.find("div", id='field_28')

		tagitems = []
		if tags:
			for item in tags.find_all("a", class_='tag'):
				tag = item.get_text().strip()
				while "  " in tag:
					tag = tag.replace("  ", " ")
				tag = tag.replace(" ", "-").lower()
				# print("Text:", tag)
				tagitems.append(tag)
		ret["tags"] = " ".join(tagitems)


		return ret

	def getItemPages(self, url):
		soup = self.wg.getSoup(url.strip(), addlHeaders={'Referer': 'http://www.surasplace.com/index.php/projects.html'})

		baseInfo = self.extractItemInfo(soup)

		ret = []

		contents = soup.find("div", class_='listing-desc')
		items = contents.find_all("td")


		for link in items:
			if not link.a:
				continue
			# print(link)
			item = {}

			item["sourceUrl"]      = link.a["href"].strip()
			item["seriesName"]     = baseInfo["title"]
			item["tags"]           = baseInfo["tags"]
			item["retreivalTime"]  = time.time()


			ret.append(item)

		return ret




	def getFeed(self):
		# for item in items:
		# 	self.log.info( item)
		#

		self.log.info( "Loading Mc Items")

		ret = []

		seriesPages = self.getSeriesPages()


		for itemUrl in seriesPages:

			itemList = self.getItemPages(itemUrl)
			for itemUrl in itemList:
				ret.append(itemUrl)

			if not runStatus.run:
				self.log.info( "Breaking due to exit flag being set")
				break
		self.log.info("Found %s total items", len(ret))
		return ret



if __name__ == "__main__":
	import utilities.testBase as tb

	with tb.testSetup():
		get = FeedLoader()
		# get.getSeriesPages()
		# get.getAllItems()
		get.go()
		# get.getItemPages('http://www.surasplace.com/index.php/projects/one-shots/27-phantom-syndrome.html')
		# get.getItemPages('http://www.surasplace.com/index.php/projects/drama/78-i-have-something-to-tell-you.html')
		# get.getItemPages('http://www.surasplace.com/index.php/projects/drama/5-useful-good-for-nothing.html')
		# get.getItemPages('http://www.surasplace.com/index.php/projects/fantasy/14-evil-queen-s-holiday.html')
		# get.getItemPages('http://www.surasplace.com/index.php/projects/fantasy/15-gods-of-time.html')
		# get.getItemPages('http://www.surasplace.com/index.php/projects/fantasy/10-dalsez.html')

