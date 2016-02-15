

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
import json

import ScrapePlugins.RetreivalDbBase
import nameTools as nt


app_user_agent = [
			('User-Agent'		,	"MangaBox"),
			('Accept-Encoding'	,	"gzip")
			]

class FeedLoader(ScrapePlugins.RetreivalDbBase.ScraperDbBase):



	loggerPath = "Main.Manga.Mbx.Fl"
	pluginName = "MangaBox.me Scans Link Retreiver"
	tableKey = "mbx"
	dbName = settings.DATABASE_DB_NAME

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	tableName = "MangaItems"

	urlBase      = "http://mangastream.com/"
	seriesBase   = "http://mangastream.com/manga"
	api_endpoint = "https://jsonrpc.mangabox.me/"


	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.jwg = webFunctions.WebGetRobust(logPath=self.loggerPath+".Web", uaOverride=app_user_agent)


	def make_base_api_request(self, params):
		header_params = {
			'Content-Type': 'application/json-rpc; charset=utf-8'
		}
		params = json.dumps(params)
		ret = self.jwg.getJson(self.api_endpoint, jsonPost=params, addlHeaders=header_params)
		return ret

	def make_api_request(self, method, params):
		postdata = {
		    "jsonrpc": "2.0",
		    "method": method,
		    "params": {
		        "device": {
		            "uid": "ff664f69f686b9cd35da1ab08683510b",
		            "os": "android",
		            "adid": "",
		            "os_ver": "4.2.2",
		            "bundle_id": "mangabox.me",
		            "UUID": "8cf467bf-7633-4915-a909-a4ca819bc92e",
		            "require_image_size": "l",
		            "aid": "79fc41b8bdcdb20b",
		            "app_build": 88,
		            "lang": "en",
		            "app_ver": "1008005",
		            "model_name": "Dickbutt Google Nexus 7 - 4.2.2 - API 17 - 800x1280"
		        },
		        "user": {
		            "locale": "en"
		        }
		    },
		    "id": method
		}
		for key, value in params.items():
			postdata['params'][key] = value


		ret = self.make_base_api_request(postdata)
		print(ret)



	def closeDB(self):
		self.log.info( "Closing DB...",)
		self.conn.close()
		self.log.info( "done")




	def extractItemInfo(self, soup):

		ret = {}
		main = soup.find('div', class_='span8')

		ret["title"] = main.h1.get_text().strip()

		return ret

	def getItemPages(self, pageUrl):
		self.log.info("Should get item for '%s'", pageUrl)

		ret = []

		soup = self.wg.getSoup(pageUrl)
		baseInfo = self.extractItemInfo(soup)

		table = soup.find('table', class_='table-striped')

		for row in table.find_all("tr"):

			if not row.td:
				continue
			if not row.a:
				continue
			chapter, ulDate = row.find_all('td')

			chapTitle = chapter.get_text().strip()

			# Fix stupid chapter naming
			chapTitle = chapTitle.replace("Ep. ", "c")

			date = dateutil.parser.parse(ulDate.get_text().strip(), fuzzy=True)

			item = {}

			url = row.a["href"]
			url = urllib.parse.urljoin(self.urlBase, url)

			item["originName"]    = "{series} - {file}".format(series=baseInfo["title"], file=chapTitle)
			item["sourceUrl"]     = url
			item["seriesName"]    = baseInfo["title"]
			item["retreivalTime"] = calendar.timegm(date.timetuple())

			if not item in ret:
				ret.append(item)

		self.log.info("Found %s chapters for series '%s'", len(ret), baseInfo["title"])
		return ret



	def getSeriesUrls(self):
		ret = set()

		soup = self.wg.getSoup(self.seriesBase)
		table = soup.find('table', class_='table-striped')

		rows = table.find_all("tr")


		for row in rows:
			if not row.td:
				continue
			series, dummy_chapName = row.find_all('td')
			if not series.a:
				continue


			ret.add(series.a['href'])

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
	fl.make_api_request(
			method = 'get_information',
			params = {
					"os": "android",
					"locale": "en"
				}
		)
	# fl.go()
	# fl.getSeriesUrls()
	# items = fl.getItemPages('http://mangastream.com/manga/area_d')
	# print("Items")
	# for item in items:
	# 	print("	", item)

