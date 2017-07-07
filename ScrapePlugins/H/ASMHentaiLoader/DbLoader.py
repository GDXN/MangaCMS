
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
import concurrent.futures

class DbLoader(ScrapePlugins.LoaderBase.LoaderBase):


	dbName = settings.DATABASE_DB_NAME
	loggerPath = "Main.Manga.ASMHentai.Fl"
	pluginName = "ASMHentai Link Retreiver"
	tableKey   = "asmh"
	urlBase    = "https://asmhentai.com/"

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	tableName = "HentaiItems"

	def loadFeed(self, pageOverride=None):
		self.log.info("Retreiving feed content...")
		if not pageOverride:
			pageOverride = 1

		url = "https://asmhentai.com/pag/{}/".format(pageOverride)

		soup = self.wg.getSoup(url, addlHeaders={"Referer" : self.urlBase})

		return soup

	def rowToTags(self, content):
		ret = []
		for item in content.find_all("a"):
			ret.append(item.get_text().strip().lower())
		return ret

	def getInfo(self, itemUrl):
		ret = {'tags' : []}
		soup = self.wg.getSoup(itemUrl)

		info_section = soup.find("div", class_='info')

		ret['originName'] = info_section.h1.get_text().strip()

		for metarow in soup.find_all("div", class_='tags'):
			sectionname = metarow.h3
			rowdat = metarow.div

			cat = sectionname.get_text().strip()
			if cat == "Uploaded:":
				rowtxt = rowdat.get_text().strip()
				ulDate = parser.parse(rowtxt).utctimetuple()

				ultime = calendar.timegm(ulDate)
				if ultime > time.time():
					self.log.warning("Clamping timestamp to now!")
					ultime = time.time()
				ret['retreivalTime'] = ultime
			elif cat == "Category:":
				tags = self.rowToTags(rowdat)
				if tags:
					ret["seriesName"] = tags[0].title()
				else:
					ret["seriesName"] = "Unknown"
			elif cat == "Artists:":
				tags = self.rowToTags(rowdat)
				tags = ["artist "+tag for tag in tags]
				ret['tags'].extend(tags)
			elif cat == "Groups:":
				tags = self.rowToTags(rowdat)
				tags = ["Group "+tag for tag in tags]
				ret['tags'].extend(tags)
			elif cat == "Collections:":
				tags = self.rowToTags(rowdat)
				tags = ["Collection "+tag for tag in tags]
				ret['tags'].extend(tags)
			elif cat == "Parody:":
				tags = self.rowToTags(rowdat)
				tags = ["Parody "+tag for tag in tags]
				ret['tags'].extend(tags)
			elif cat == "Characters:":
				tags = self.rowToTags(rowdat)
				tags = ["Character "+tag for tag in tags]
				ret['tags'].extend(tags)
			elif cat == "Tags:":
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
			elif cat == "Language:":
				tags = self.rowToTags(rowdat)
				tags = ["Language "+tag for tag in tags]
				ret['tags'].extend(tags)

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

		ret['tags'] = " ".join(ret['tags'])

		# print("Series metadata: ", ret)
		return ret


	def parseItem(self, containerDiv, retag):
		ret = {}
		ret['sourceUrl'] = urllib.parse.urljoin(self.urlBase, containerDiv.a["href"])

		# Do not decend into items where we've already added the item to the DB
		rowd = self.getRowsByValue(sourceUrl=ret['sourceUrl'])
		if len(rowd) and not retag:
			return None
		if not len(rowd) and retag:
			return None

		ret.update(self.getInfo(ret['sourceUrl']))

		# Yaoi isn't something I'm that in to.
		if "yaoi" in ret["tags"]:
			self.log.info("Yaoi item. Skipping.")
			return None

		return ret

	def update_tags(self, items):
		for item in items:
			rowd = self.getRowsByValue(sourceUrl=item["sourceUrl"], limitByKey=False)
			if rowd:
				self.log.info("Updating tags for %s", item['sourceUrl'])
				self.addTags(sourceUrl=item['sourceUrl'], tags=item['tags'])

	def getFeed(self, pageOverride=None, filter_eng=True, time_offset=0, retag=False):
		# for item in items:
		# 	self.log.info(item)
		#

		soup = self.loadFeed(pageOverride)


		divs = soup.find_all("div", class_='preview_item')

		ret = []

		for itemDiv in divs:
			cap = itemDiv.find("div", class_='caption')
			if cap.img['src'] == "/images/en.png" or filter_eng != True or retag:
				item = self.parseItem(itemDiv, retag)
				if item:

					item['retreivalTime'] = time.time() - time_offset
					ret.append(item)

		if retag:
			self.update_tags(ret)
			ret = []
		return ret

def process(runner, pageOverride, time_offset, retag=False):
	print("Executing with page offset: pageOverride")
	res = runner.getFeed(pageOverride=pageOverride, filter_eng=False, time_offset=time_offset, retag=retag)
	print("Received %s results!" % len(res))
	runner._processLinksIntoDB(res)


def getHistory(retag=False):
	print("Getting history")
	run = DbLoader()
	with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
		futures = [executor.submit(process, runner=run, pageOverride=x, time_offset=time.time(), retag=retag) for x in range(0, 8980)]
		print("Waiting for executor to finish.")
		executor.shutdown()

def test():
	print("Test!")
	run = DbLoader()

	dat = run.getFeed(retag=True)
	print(dat)
	# print(run.go())
	# print(run)
	# pprint.pprint(run.getFeed())

	# print(run.getInfo("https://asmhentai.com/g/178575/"))

if __name__ == "__main__":
	import utilities.testBase as tb

	with tb.testSetup(load=False):
		getHistory(retag=True)
		# test()
		# run = DbLoader()
		# run.go()


