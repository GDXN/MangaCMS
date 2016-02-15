

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

'''

## MangaBox API:

This is entirely derived from sniffing the calls the app makes
with a HTTPS decrypting proxy, after breaking cert pinning on the
android install. No guarantees, YMMV. Writing your own client may
get MangaBox people angry, set your cat on fire, etc....

All API functions operate by POSTing to https://jsonrpc.mangabox.me with
content-type "application/json-rpc; charset=utf-8".

Currently, the MangaBox app makes a couple POST requests at start that
return 400 or 504 errors. This could be some sort of clever port-knocking
type session initialization, but it's probably safer to assume it's just broken
shit.

Example headers:
	POST https://jsonrpc.mangabox.me/ HTTP/1.1
	User-Agent: MangaBox
	Content-Type: application/json-rpc; charset=utf-8
	Content-Length: 449
	Host: jsonrpc.mangabox.me
	Connection: Keep-Alive
	Accept-Encoding: gzip

Responses are also JSON, generally gzipped:
	HTTP/1.1 200 OK
	Date: Sun, 14 Feb 2016 04:09:50 GMT
	Server: MangaBox/20131204
	Content-Type: application/json; charset=utf8
	X-JSONRPC-METHOD: get_magazines
	X-MJ-UID: ff664f69f686b9cd35da1ab08683510b
	X-Request-Id: c3722a57d600
	Vary: Accept-Encoding
	Content-Length: 3901
	Connection: close

All POST requests have some common features:

	{
	    "jsonrpc": "2.0",
	    "method": "get_information",
	    "params": {
	        "os": "android",
	        "locale": "en",
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
	            "model_name": "Genymotion Google Nexus 7 - 4.2.2 - API 17 - 800x1280"
	        },
	        "user": {
	            "locale": "en"
	        }
	    },
	    "id": "get_information"
	}

The relevant actual API params are "method", "id", "params"["os"] and "params"["locale"].
"params"["device"] and "params"["user"] appear to be included in all API requests.

Note that the API method is actually present twice - as "method" and "id". This appears
to be intentional.


API call responses have a similar structure:
	{
	    "jsonrpc": "2.0",
	    "id": "get_app_status",
	    "result": {
	        < -- snip -- >
	    }
	}
	the "id" field just returns the API call name. Apparently we're currently on
	API version 2. The contents of the "result" field can be a object or a list,
	depending on API call

------

Observed API calls

# Get recent blog posts (?)
	This appears to be the "news" feed for MangaBox. Probably ignorable.

	Note that I've seen this apparently used to push pop-up notifications
	upon app launch (I think).

	Params:
		"method"/"id"      - "get_information"
		"params"->"locale" - "en"
	Return:
		{
		    "jsonrpc": "2.0",
		    "id": "get_information",
		    "result": [{
		        "updatedDate": 1392208425,
		        "publishedDate": 1392206430,
		        "url": "https://www.mangabox.me/information/5/",
		        "title": "Several Manga have been temporarily removed from t",
		        "type": "2",
		        "id": "5",
		        "expiredDate": 1423742430
		    }, {
		        "updatedDate": 1392820781,
		        "publishedDate": 1392850800,
		        "url": "https://www.mangabox.me/information/7/",
		        "title": "Chinese support",
		        "type": "3",
		        "id": "7",
		        "expiredDate": 1424300400
		    }, {
		        "updatedDate": 1396370411,
		        "publishedDate": 1396360800,
		        "url": "https://www.mangabox.me/information/11/",
		        "title": "Regarding the Publication Status of Several Manga",
		        "type": "2",
		        "id": "11",
		        "expiredDate": 1427896800
		    }, {
		        "updatedDate": 1417582096,
		        "publishedDate": 1417575600,
		        "url": "https://www.mangabox.me/information/57/",
		        "title": "Access to some manga where it is out of Japan",
		        "type": "3",
		        "id": "57",
		        "expiredDate": 2996060400
		    }]
		}

# Get App Status:
	I'm not sure what this is supposed to do, exactly. It appears to return
	some status information about what capabilities the app is supposed
	to do.

	Some of the flags are interesting. I'd assume "force_update" prevents the
	clients from operating untill the app is updated.
	"store"->"store_on" indicates there is a store, either planned or I just
	haven't noticed it yet (I actually haven't /used/ the app much).

	"indies_on" is interesting, but I can't figure out if it's a toggleable
	setting /in/ the app.

	Params:
		"method"/"id" - "get_app_status"
		"params"->"first_launch" - "0" (presumably 1 on first launch)
	Return:
		{
		    "jsonrpc": "2.0",
		    "id": "get_app_status",
		    "result": {
		        "recommend_on": 0,
		        "time": 1455419589,
		        "indies": {
		            "search": {
		                "enable": 1,
		                "path": "search"
		            },
		            "pre_read_tutorial_on": 0,
		            "unlock_coin_on": 0,
		            "coach_mark": {
		                "threshold_manga_count": 4,
		                "threshold_days": 7
		            }
		        },
		        "get_delta_on": 0,
		        "ad": {
		            "five": {
		                "loading_enabled_only_wifi": 0,
		                "five_on": 0,
		                "playback_enabled_only_wifi": 0
		            }
		        },
		        "indies_on": 0,
		        "recommend_first_on": 0,
		        "get_delta_v2_on": 1,
		        "force_update": {
		            "required": 0
		        },
		        "review_approach_type": 0,
		        "unlock": {
		            "unlock_coin_on": 0
		        },
		        "peak_time_log_limit_on": 1,
		        "store": {
		            "store_on": 0
		        },
		        "unlock_on": 1,
		        "langs": {
		            "en": "English",
		            "ja": "日本語",
		            "zh": "繁體中文"
		        },
		        "auser": {
		            "auser_on": 0
		        }
		    }
		}

# Get Magazines:
	This seems to be for querying the "magazines" available
	to the client. It appears mangabox logically groups sets of
	chapter releases into a magazine, presumably mimicing
	the traditional publishing approach.


	Params:
		"method"/"id"              - "get_magazines"
		"params"->"locale"         - "en"
		"params"->"is_include_all" - "1"
			I'm not sure what this does, it's possible it's part of
			pagination support that's not currently implemented.
	Return:

		{
		    "jsonrpc": "2.0",
		    "id": "get_magazines",
		    "result": [{
		        "volumeDisplayYear": "2014",
		        "volume": "0",
		        "contentsCount": "64",
		        "wide_grids": [],
		        "updatedDate": 1425387076,
		        "publishDate": 1393340400,
		        "expireDate": 1456412400,
		        "appearDate": 1393340400,
		        "id": "33",
		        "title": "Digest",
		        "volumeDisplayNumber": "0"
		    }, {
		        "volumeDisplayYear": "2015",
		        "volume": "105",
		        "contentsCount": "12",
		        "wide_grids": [],
		        "updatedDate": 1447050933,
		        "publishDate": 1448377200,
		        "expireDate": 1455634800,
		        "appearDate": 1447772400,
		        "id": "305",
		        "title": "mangabox vol.52",
		        "volumeDisplayNumber": "52"
		    },
		         < - - snip a pile more entries - - >
		    ]
		}

	Each "magazine" seems to have a unique ID (the "id" field) that is used later.
	The "digest" magazine is, I believe a overview of what's happened in the
	various series leading up to the currently available releases.
	The date fields are unix timestamps.
	"wide_grids" is empty in every currently available magazine, so it's
	function is unknown.
	The "volumeDisplayYear" field appears to be a shortcut for some of the display
	widgets, so that the client doesn't have to extract the year from the unix
	time stamp. Yes, it seems pretty silly.
	It also seems broken, in that every current volume, even ones released last year
	are labeled "2016".

	Lastly, it appears that the "title" is incorrect, particularly since what I think is the first
	volume is somehow labelled 52.

# Get Delta:
	I *think* this is to allow the client to only re-load content
	that has changed since the last app startup.


	Params:
		"method"/"id"                 - "get_delta_v2"
		"params"->"times"->"manga"    - "1453261351"
		"params"->"times"->"content"  - "1455268306"
		"params"->"times"->"magazine" - "1455007253"
	Return:
		{
		    "jsonrpc": "2.0",
		    "id": "get_delta_v2",
		    "result": {
		        "magazine": {
		            "deleted": [],
		            "updated": []
		        },
		        "manga": {
		            "deleted": [{
		                "date": 1455089107,
		                "id": 184
		            }, {
		                "date": 1455089232,
		                "id": 266
		            }],
		            "updated": []
		        },
		        "content": {
		            "deleted": [],
		            "updated": []
		        }
		    }
		}

# Get Magazine content:
	This appears to be one of the main API calls of interest.
	It fetches the releases for a logical "magazine".

	The value of the "contentSize" param is interesting. I don't know what it does,
	but it's possible that the client can load larger files for devices with larger
	screens, or something?

	I'll have to set up a virtual device with a high-dpi screen to test.

	NOTE: This POST request is packed in a list, e.g. [{things}], rather then
	{things} like the rest. I don't know why.

	Params:
		"method"/"id"           - "get_contents_by_magazine_id"
		"params"->"contentSize" -  "1"
		"params"->"magazineId"  - {ID For magazine}
	Return:
		{
		    "jsonrpc": "2.0",
		    "id": 335,
		    "result": [{
		        "gridState": "2",
		        "availableDate": 1453906800,
		        "position": "left",
		        "anchorPosition": "",
		        "updatedDate": 1453981173,
		        "url": "",
		        "episode": {
		            "volume": "106",
		            "manga": {
		                "authors": [{
		                    "name": "Tsuina Miura",
		                    "id": "52",
		                    "role": "Story"
		                }, {
		                    "name": "Takahiro Ohba",
		                    "id": "53",
		                    "role": "Art"
		                }],
		                "comicsCompleted": "0",
		                "visibility": 0,
		                "serialType": 0,
		                "storeTopIndex": "0",
		                "storeTopThumbURL": "https://image-a.mangabox.me/static/content/images/l/comics_thumb/comics_thumb_38.png?1426154273",
		                "excludeDeltaUpdate": "0",
		                "tags": [],
		                "womensRankIndex": 0,
		                "updatedDate": 1426154273,
		                "searchKeyword": "",
		                "createdDate": 1385095010,
		                "id": "38",
		                "mensRankIndex": 0,
		                "title": "High-rise Invasion"
		            },
		            "type": "episode",
		            "ribbon": "1"
		        },
		        "id": "15993",
		        "gridImageURL": "https://image-a.mangabox.me/static/content/images/l/magazine_content_grid/335/grid_15993.png?1452774361",
		        "mask": "117",
		        "numPages": "16",
		        "magazineId": "335",
		        "publishDate": 1454511600,
		        "index": "1",
		        "baseUrl": "https://image-a.mangabox.me/static/content/magazine/335/l/fa7f2efed3563ed6cc23361f8cac913e425c17a8e2783f3c3bc9bf8abdfca3cf/webp",
		        "coverSize": "2",
		        "expiredDate": 1461682800
		    }, {
		        "gridState": 0,
		        "availableDate": 1453906800,
		        "position": "left",
		        "anchorPosition": "",
		        "updatedDate": 1454403397,
		        "url": "",
		        "episode": {
		            "volume": "31",
		            "manga": {
		                "authors": [{
		                    "name": "Yukari Koyama",
		                    "id": "298",
		                    "role": "Story"
		                }, {
		                    "name": "Eriza Kusakabe",
		                    "id": "299",
		                    "role": "Art"
		                }],
		                "comicsCompleted": "0",
		                "visibility": 0,
		                "serialType": 0,
		                "storeTopIndex": "0",
		                "storeTopThumbURL": "https://image-a.mangabox.me/static/content/images/l/comics_thumb/comics_thumb_238.png?1419242701",
		                "excludeDeltaUpdate": "0",
		                "tags": [],
		                "womensRankIndex": 0,
		                "updatedDate": 1419242701,
		                "searchKeyword": "",
		                "createdDate": 1411380615,
		                "id": "238",
		                "mensRankIndex": 0,
		                "title": "HOLIDAY LOVE"
		            },
		            "type": "episode",
		            "ribbon": "1"
		        },
		        "id": "15994",
		        "gridImageURL": "https://image-a.mangabox.me/static/content/images/l/magazine_content_grid/335/grid_15994.png?1452825486",
		        "mask": "-118",
		        "numPages": "18",
		        "magazineId": "335",
		        "publishDate": 1454511600,
		        "index": "2",
		        "baseUrl": "https://image-a.mangabox.me/static/content/magazine/335/l/7cf3b4529a211741eed857e4d7224d12f78bb8b2b3b389da90c56641f843df91/webp",
		        "coverSize": "2",
		        "expiredDate": 1458140400
		    },
		        < - - Snip a bunch of entries - - >
		    ]
		}

		Here we have a much more interesting item. Individual chapters are broken out into discrete objects.

		Of interest is the "baseUrl" param, which is the base for the generated URLs for the series.

		Additionally, the "mask" param is interesting. I suspect (admittedly based on nothing, at the moment) that
		it encodes the mask XORed with each byte of the images to make them valid.
		Fortunately, we can skip that because they're serving webp images, which means the first 12 bytes are
		always "RIFFxxxxWEBP", where xxxx is the file size. As such, since the protection is just a fixed
		XORed byte, we can just determine it from the first 4 bytes by XORing them with the actual content
		("RIFF").

		The "title" field is the title of the manga series. "volume" appears to be the chapter release, called
		"Ep." in the app (confusing much?).

		Lastly, the "updatedDate" field is relevant, because it gets passed as a param in the image requests.

# Fetching images:
	Retreiving the images for a release is /fairly/ straight forward.

	First, the 'baseUrl" field is taken. Then, to get the list of image names,
		>- {baseurl} + "/" + "filenames.txt" + "?" + {updatedDate}

	This returns a extremely simple text-file:
		001.webp
		002.webp
		003.webp
		004.webp
		005.webp
		006.webp
		007.webp
		008.webp
		009.webp
		010.webp

	Each of the images described in the text file are then requested similarly:
		>- {baseurl} + "/" + {image name} + "?" + {updatedDate}

	Note that the MangaBox client is quite aggressive with prefetching, it downloads every
	page in a series as soon as it's opened. Presumably, emulating this behavour should therefore
	be harmless.


	Note that requests for the images/filenames.txt are done using the default device user-agent, rather
	then the "MangaBox" user-agent that's used for all API requests.

'''


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

