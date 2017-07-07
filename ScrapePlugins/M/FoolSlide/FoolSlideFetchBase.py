
import bs4

import time
import dateutil.parser
import runStatus
import parsedatetime
import calendar
import datetime

import ScrapePlugins.LoaderBase


import abc

class FoolFeedLoader(ScrapePlugins.LoaderBase.LoaderBase):


	@abc.abstractmethod
	def urlBase(self):
		return None
	@abc.abstractmethod
	def feedUrl(self):
		return None

	# Can be overridden by child-classes, to allow filtering of
	# downloads
	def filterItem(self, item):
		return item


	def extractItemInfo(self, soup):

		ret = {}

		infoDiv = soup.find("div", class_='large comic')

		# titleDiv = soup.find("h1", class_="ttl")
		ret["title"] = infoDiv.find("h1", class_='title').get_text().strip()

		return ret

	def extractDate(self, inStr):
		try:
			date = dateutil.parser.parse(inStr, fuzzy=True)
			return date
		except ValueError:
			pass


		cal = parsedatetime.Calendar()
		ulDate, ign_status = cal.parse(inStr)
		# print(ulDate)
		ultime = datetime.datetime.fromtimestamp(calendar.timegm(ulDate))

		# No future times!
		if ultime > datetime.datetime.now():
			self.log.warning("Clamping timestamp to now!")
			ultime = datetime.datetime.now()
		return ultime



	def getItemPages(self, url):
		self.log.info("Should get item for '%s'", url)
		page = self.wg.getpage(url)

		if "This series contains mature contents and is meant to be viewed by an adult audience." in page:
			self.log.info("Adult check page. Confirming...")
			page = self.wg.getpage(url, postData={"adult": "true"})


		soup = bs4.BeautifulSoup(page, "lxml")


		baseInfo = self.extractItemInfo(soup)

		ret = []

		for itemDiv in soup.find_all("div", class_="element"):
			item = {}
			linkDiv = itemDiv.find('div', class_='title')
			link = linkDiv.a

			url = link["href"]
			chapTitle = link.get_text().strip()

			chapDate = itemDiv.find("div", class_="meta_r")



			date = self.extractDate(chapDate.a.next_sibling.strip(", "))


			item["originName"] = "{series} - {file}".format(series=baseInfo["title"], file=chapTitle)
			item["sourceUrl"]  = url
			item["seriesName"] = baseInfo["title"]
			item["retreivalTime"]       = calendar.timegm(date.timetuple())

			item = self.filterItem(item)
			if item:
				ret.append(item)

		return ret



	def getSeriesUrls(self):
		ret = []

		pageNo = 1
		while 1:
			pageUrl = self.feedUrl.format(num=pageNo)
			page = self.wg.getSoup(pageUrl)
			itemDivs = page.find_all("div", class_='group')

			hadNew = False

			for div in itemDivs:
				link = div.a["href"]
				if not link in ret:
					hadNew = True
					ret.append(link)

			if not hadNew:
				break

			pageNo += 1

		return ret


	def getFeed(self):
		# for item in items:
		# 	self.log.info( item)
		#

		self.log.info( "Loading Items")

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



