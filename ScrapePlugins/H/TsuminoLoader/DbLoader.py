
import webFunctions

import pprint
import calendar
import traceback

from dateutil import parser
import settings
import parsedatetime
import urllib.parse
import time
import calendar

import ScrapePlugins.LoaderBase
class DbLoader(ScrapePlugins.LoaderBase.LoaderBase):


	dbName = settings.DATABASE_DB_NAME
	loggerPath = "Main.Manga.Tsumino.Fl"
	pluginName = "Tsumino Link Retreiver"
	tableKey    = "ts"
	urlBase = "http://www.tsumino.com/"

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	tableName = "HentaiItems"

	def loadFeed(self, pageOverride=None):
		self.log.info("Retreiving feed content...",)
		if not pageOverride:
			pageOverride = 1

		try:
			page_params = {
				"PageNumber"         : pageOverride,
				"Search"             : "",
				"SortOptions"        : "Newest",
				"PageMinimum"        : 1,
				"PageMaximum"        : 2150,
				"RateMinimum"        : 0,
				"RateMaximum"        : 5,
				"ExcludeCategories"  : "false",
				"ExcludeArtists"     : "false",
				"ExcludeGroups"      : "false",
				"ExcludeParodies"    : "false",
				"ExcludeCollections" : "false",
				"ExcludeCharacters"  : "false",
				"ExcludeUploaders"   : "false",
			}

			referrer = "http://www.tsumino.com/?PageNumber={num}".format(num=pageOverride)

			soup = self.wg.getJson("http://www.tsumino.com/Browse/Query", postData=page_params, addlHeaders={"Referer" : referrer})
		except urllib.error.URLError:
			self.log.critical("Could not get page from Tsumino!")
			self.log.critical(traceback.format_exc())
			return None

		return soup


	def getCategoryTags(self, soup):
		tagChunks = soup.find_all('div', class_='field-name')
		tags = []
		category = "None"



		# 'Origin'       : '',  (Category)
		for chunk in tagChunks:
			for rawTag in chunk.find_all("a", class_='tag'):
				if rawTag.span:
					rawTag.span.decompose()
				tag = rawTag.get_text().strip()

				if "Artist" in chunk.contents[0]:
					category = "Artist-"+tag.title()
					tag = "artist "+tag
				tag = tag.replace("  ", " ")
				tag = tag.replace(" ", "-")
				tags.append(tag)

		tags = " ".join(tags)
		return category, tags
	def rowToTags(self, content):
		ret = []
		for item in content.find_all("a", class_='book-tag'):
			ret.append(item.get_text().strip().lower())
		return ret

	def getInfo(self, itemUrl):
		ret = {'tags' : []}
		soup = self.wg.getSoup(itemUrl)

		for metarow in soup.find_all("div", class_='book-line'):
			items = metarow.find_all("div", recursive=False)
			assert len(items) == 2

			rowname, rowdat = items

			cat = rowname.get_text().strip()
			if cat == "Title":
				ret['originName'] = rowdat.get_text().strip()

			elif cat == "Uploaded":
				rowtxt = rowdat.get_text().strip()
				ulDate = parser.parse(rowtxt).utctimetuple()

				ultime = calendar.timegm(ulDate)
				if ultime > time.time():
					self.log.warning("Clamping timestamp to now!")
					ultime = time.time()
				ret['retreivalTime'] = ultime
			elif cat == "Category":
				tags = self.rowToTags(rowdat)
				if tags:
					ret["seriesName"] = tags[0]
				else:
					ret["seriesName"] = "Unknown"
			elif cat == "Artist":
				tags = self.rowToTags(rowdat)
				tags = ["artist "+tag for tag in tags]
				ret['tags'].extend(tags)
			elif cat == "Groups":
				tags = self.rowToTags(rowdat)
				tags = ["Group "+tag for tag in tags]
				ret['tags'].extend(tags)
			elif cat == "Collections":
				tags = self.rowToTags(rowdat)
				tags = ["Collection "+tag for tag in tags]
				ret['tags'].extend(tags)
			elif cat == "Parody":
				tags = self.rowToTags(rowdat)
				tags = ["Parody "+tag for tag in tags]
				ret['tags'].extend(tags)
			elif cat == "Characters":
				tags = self.rowToTags(rowdat)
				tags = ["Character "+tag for tag in tags]
				ret['tags'].extend(tags)
			elif cat == "Tags":
				tags = self.rowToTags(rowdat)
				ret['tags'].extend(tags)


			# Garbage stuff
			elif cat == "Pages":
				pass
			elif cat == "Rating":
				pass
			elif cat == "My Rating":
				pass
			elif cat == "Uploader":
				pass

			# The "Download" row has an empty desc
			elif cat == "":
				pass
			else:
				raise RuntimeError("Unknown category tag: '{}' -> '{}'".format(cat, rowdat.prettify()))


		while any(["  " in tag for tag in ret['tags']]):
			ret['tags'] = [tag.replace("  ", " ") for tag in ret['tags']]
		ret['tags'] = [tag.replace(" ", "-") for tag in ret['tags']]
		ret['tags'] = [tag.lower() for tag in ret['tags']]

		# Colons break the tsvector
		ret['tags'] = [tag.replace(":", "-") for tag in ret['tags']]

		return ret


	def parseItem(self, containerDiv):
		ret = {}
		ret['sourceUrl'] = urllib.parse.urljoin(self.urlBase, containerDiv.a["href"])

		# Do not decend into items where we've already added the item to the DB
		if len(self.getRowsByValue(sourceUrl=ret['sourceUrl'])):
			return None

		ret.update(self.getInfo(ret['sourceUrl']))

		# Yaoi isn't something I'm that in to.
		if "yaoi" in ret["tags"]:
			self.log.info("Yaoi item. Skipping.")
			return None

		return ret

	def getFeed(self, pageOverride=None):
		# for item in items:
		# 	self.log.info(item)
		#

		jdat = self.loadFeed(pageOverride)
		markup = jdat['Data']

		soup = webFunctions.as_soup(markup)

		divs = soup.find_all("div", class_='book-grid-item-container')

		ret = []
		for itemDiv in divs:

			item = self.parseItem(itemDiv)
			if item:
				ret.append(item)


		return ret


def getHistory():

	run = DbLoader()
	# dat = run.getFeed()
	# print(dat)
	for x in range(0, 700):
		dat = run.getFeed(pageOverride=x)
		run.processLinksIntoDB(dat)

def test():
	print("Test!")
	run = DbLoader()
	print(run.go())
	# print(run)
	# pprint.pprint(run.getFeed())
	# pprint.pprint(run.getInfo("http://www.tsumino.com/Book/Info/27698/1/sleeping-beauty-dornroschen"))
	pass

if __name__ == "__main__":
	import utilities.testBase as tb

	with tb.testSetup(load=False):
		getHistory()
		# test()
		# run = DbLoader()
		# run.go()


