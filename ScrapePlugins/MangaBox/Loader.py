
import time
import zipfile
import settings
import traceback
import json
import os.path

import logSetup
import runStatus
if __name__ == "__main__":
	logSetup.initLogging()
	runStatus.preloadDicts = False

import webFunctions
import processDownload
import ScrapePlugins.RetreivalDbBase
import nameTools as nt

app_user_agent = [
			('User-Agent'		,	"MangaBox"),
			('Accept-Encoding'	,	"gzip")
			]

app_browser_ua = [
			('User-Agent'		,	"Dalvik/1.6.0 (Linux; U; Android 4.2.2; Google Nexus 7 - 4.2.2 - API 17 - 800x1280 Build/JDQ39E) MangaBox (android, com.dena.mj)"),
			('Accept-Encoding'	,	"gzip, deflate")
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

	Excepting the time field, the return values are identical for a device with a 2560*1600 screen.

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

	The retreived images are encrypted.

	Png header chunks:
		Expected: 89 50 4e 47    0d 0a 1a 0a
		Recieved: c0 19 d7 de    9a 9d 9a 8a
		XOR:      49 49 99 99    97 97 80 80

	Another sample (jpg):
		Expected: b8 9f 80 9f
		Recieved: ff d8 ff
		XOR:      47 47 7f


	Another sample (webp):
		Expected: 52 49 46 46 -- -- -- -- 57 45 42 50 56 50 38 20
		Recieved: 7e 65 71 71 -- -- -- -- 72 60 67 75 67 61 17 0f
		XOR:      2c 2c 37 37 -- -- -- -- 25 25 25 25 31 31 2f 2f

	Scraped via proxy (webp):
		Expected: 52 49 46 46 -- -- -- -- 57 45 42 50 56 50 38 20
		Recieved: 41 5a 4e 4e -- -- -- -- 4d 5f 58 4a 58 5e 28 30
		XOR:      13 13 08 08 -- -- -- -- 1a 1a 1a 1a 0e 0e 10 10

	It looks like every 2 bytes are XOR with a rolling value.
	How the rolling value is generated is not currently certain.


'''


class Loader(ScrapePlugins.RetreivalDbBase.ScraperDbBase):



	loggerPath = "Main.Manga.Mbx.Fl"
	pluginName = "MangaBox.me Scans Link Retreiver"
	tableKey = "mbx"
	dbName = settings.DATABASE_DB_NAME


	tableName = "MangaItems"

	urlBase      = "http://mangastream.com/"
	seriesBase   = "http://mangastream.com/manga"
	api_endpoint = "https://jsonrpc.mangabox.me/"


	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.wg  = webFunctions.WebGetRobust(logPath=self.loggerPath+".Web", uaOverride=app_browser_ua)
		self.jwg = webFunctions.WebGetRobust(logPath=self.loggerPath+".Web", uaOverride=app_user_agent)


	def make_base_api_request(self, params=None, param_str=None):

		if params and param_str:
			raise ValueError("Wat?")
		if not (params or param_str):
			raise ValueError("Watt?")

		header_params = {
			'Content-Type': 'application/json-rpc; charset=utf-8'
		}
		if params:
			params = json.dumps(params)
		else:
			params = param_str
		# print(params)
		ret = self.jwg.getJson(self.api_endpoint, jsonPost=params, addlHeaders=header_params)
		return ret

	def make_api_request(self, *args, **kwargs):
		postdata = self.pack_api_request(*args, **kwargs)

		# pprint.pprint(postdata)

		ret = self.make_base_api_request(postdata)
		return ret

	def pack_api_request(self, method, params, root_id_override=None, pack_in_list=False):
		if root_id_override is None:
			root_id = method
		else:
			root_id = root_id_override
		postdata = {
		    "jsonrpc": "2.0",
		    "method": method,
		    "params": {
		        "device": {
		            "uid": "5e264d04e1d8aaa5741ba89f26888bc7",
		            "os": "android",
		            "adid": "",
		            "os_ver": "4.2.2",
		            "bundle_id": "mangabox.me",
		            "UUID": "052a4e19-12ae-403a-862d-7ff999eb136e",
		            "require_image_size": "l",
		            "aid": "b7521aa854d72c44",
		            "app_build": 88,
		            "lang": "en",
		            "app_ver": "1008005",
		            "model_name": "Genymotion Google Nexus 10 - 4.2.2 - API 17 - 2560x1600"
		        },
		        "user": {
		            "locale": "en"
		        }
		    },
		    "id": root_id
		}
		for key, value in params.items():
			postdata['params'][key] = value

		if pack_in_list:
			postdata = [postdata,]

		return postdata

	def closeDB(self):
		self.log.info( "Closing DB...",)
		self.conn.close()
		self.log.info( "done")


	def getFileInfo(self, chapter_obj):

		url = chapter_obj['baseUrl'] + "/" + "filenames.txt" + "?" + str(chapter_obj['updatedDate'])
		ret = self.wg.getpage(url)
		ret = ret.split()
		ret = [
			(tmp, chapter_obj['baseUrl'] + "/" + tmp + "?" + str(chapter_obj['updatedDate']))
			for
				tmp
			in
				ret
			]

		return ret




	def getMagazineContent(self, mag_id):
		vals = self.make_api_request("get_contents_by_magazine_id", {
				"magazineId"  : mag_id,
				"contentSize" : "l",
				"locale"      : "en",
			},
			root_id_override=mag_id,
			pack_in_list=True)


		assert "result" in vals
		assert isinstance(vals['result'], list)
		assert all([isinstance(tmp['episode'], dict) for tmp in vals['result']])

		ret = [
			{
				"chapter"     : int(mag['episode']['volume']),
				"title"       : mag['episode']['manga']['title'],
				"updatedDate" : mag['episode']['manga']['updatedDate'],
				"xor_key"     : int(mag['mask']),
				"baseUrl"     : mag['baseUrl'],
			}
			for mag in vals['result']
		]
		return ret

	def get_image(self, imageurl, xor_key):
		ctnt = self.wg.getpage(imageurl)

		# Fix sign issues in the byte mask.
		if xor_key < 0:
			xor_key += 256

		# "Decrypt" the file
		cont_o = bytes([b ^ xor_key for b in ctnt])

		return cont_o


	def getFile(self, file_data):


		row = self.getRowsByValue(sourceUrl=file_data["baseUrl"], limitByKey=False)
		if row and row[0]['dlState'] != 0:
			return
		if not row:
			self.insertIntoDb(retreivalTime = time.time(),
								sourceUrl   = file_data["baseUrl"],
								originName  = file_data["title"],
								dlState     = 1,
								seriesName  = file_data["title"])

		image_links = self.getFileInfo(file_data)

		images = []
		for imagen, imageurl in image_links:
			imdat = self.get_image(imageurl, file_data['xor_key'])
			images.append((imagen, imdat))

			# filen = nt.makeFilenameSafe(file_data['title'] + " - " + imagen)
			# with open(filen, "wb") as fp:
			# 	fp.write(imdat)




		fileN = '{series} - c{chapNo:03.0f} [MangaBox].zip'.format(series=file_data['title'], chapNo=file_data['chapter'])
		fileN = nt.makeFilenameSafe(fileN)

		dlPath, newDir = self.locateOrCreateDirectoryForSeries(file_data["title"])
		wholePath = os.path.join(dlPath, fileN)


		if newDir:
			self.updateDbEntry(file_data["baseUrl"], flags="haddir")
			self.conn.commit()

		arch = zipfile.ZipFile(wholePath, "w")
		for imageName, imageContent in images:
			arch.writestr(imageName, imageContent)
		arch.close()

		self.log.info("Successfully Saved to path: %s", wholePath)

		dedupState = processDownload.processDownload(file_data["title"], wholePath, deleteDups=True)
		if dedupState:
			self.addTags(sourceUrl=file_data["baseUrl"], tags=dedupState)

		self.updateDbEntry(file_data["baseUrl"], dlState=2, downloadPath=dlPath, fileName=fileN, originName=fileN)

		self.conn.commit()
		self.log.info( "Done")



	def getMagazines(self):
		vals = self.make_api_request("get_magazines", {
				"locale"         : "en",
				"is_include_all" : "1",
			})

		assert "result" in vals
		assert isinstance(vals['result'], list)


		ret = [
			{
				"id" : int(mag['id']),
				"title" : mag['title'],
			}
			for mag in vals['result']
		]

		# Do not scrape the "digest" magazine
		ret = [tmp for tmp in ret if not "digest" in tmp['title'].lower()]

		return ret


	def reset_failed(self):
		# Force every failed fetch to retrigger, in case it has become available.
		with self.conn.cursor() as cur:
			with ScrapePlugins.RetreivalDbBase.transaction(cur, commit=True):
				cur.execute("UPDATE mangaitems SET dlstate=0  WHERE sourcesite='mbx' AND dlstate < 2;")


	def go(self):
		self.reset_failed()
		mag_nums = self.getMagazines()
		for mag in mag_nums:
			try:
				cont = self.getMagazineContent(mag['id'])
			except Exception:
				self.log.error("Wat?")
				for line in traceback.format_exc().split("\n"):
					self.log.error(line)
			for release in cont:

				try:
					self.getFile(release)
				except Exception:
					self.log.error("Wat?")
					for line in traceback.format_exc().split("\n"):
						self.log.error(line)
					self.updateDbEntry(release["baseUrl"], dlState=-1)

				if not runStatus.run:
					return


if __name__ == '__main__':


	fl = FeedLoader()


	# mags = fl.getMagazines()
	# for mag in mags:
	# 	print(mag)
	# 	pprint.pprint(fl.getMagazineContent(mag['id']))

	# cont = fl.getMagazineContent(33)

	# for release in cont:
	# 	fl.getFile(release)


	# data = fl.getFileInfo(params)
	# print(data)
	# for fname, url in data:
	# 	ctnt = fl.wg.getpage(url)
	# 	with open(fname+".bin", "wb") as fp:
	# 		fp.write(ctnt)


	# fl.go()
	# fl.getSeriesUrls()
	# items = fl.getItemPages('http://mangastream.com/manga/area_d')
	# print("Items")
	# for item in items:
	# 	print("	", item)

