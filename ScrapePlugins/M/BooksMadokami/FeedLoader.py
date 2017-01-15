
import webFunctions
import html.parser
import urllib.parse
import urllib.error
import time
import settings
import re
import os.path
import ScrapePlugins.RetreivalDbBase
import ScrapePlugins.RunBase
import nameTools as nt
from concurrent.futures import ThreadPoolExecutor

MASK_PATHS = [


	'/mango/Admin%20cleanup',
	'/mango/Info',
	'/mango/Manga',
	'/mango/Misc',
	'/mango/Raws',
	'/mango/Requests',
	'/mango/READ.txt',

	'/Admin%20cleanup',
	'/Info',
	'/Manga',
	'/Misc',
	'/Raws',
	'/Requests',
	'/READ.txt',


]

STRIP_PREFIX = "/mango"

HTTPS_CREDS = [
	("manga.madokami.com", settings.mkSettings["login"], settings.mkSettings["passWd"]),
	("http://manga.madokami.com", settings.mkSettings["login"], settings.mkSettings["passWd"]),
	("https://manga.madokami.com", settings.mkSettings["login"], settings.mkSettings["passWd"]),
	]

class FeedLoader(ScrapePlugins.RetreivalDbBase.ScraperDbBase):

	wg = webFunctions.WebGetRobust(creds=HTTPS_CREDS)
	loggerPath = "Main.Books.Mk.Fl"
	pluginName = "Books.Madokami Link Retreiver"
	tableKey = "mk"
	dbName = settings.DATABASE_DB_NAME

	tableName = "BookItems"
	url_base     = "https://manga.madokami.com/"
	tree_api     = "https://manga.madokami.com/stupidapi/lessdumbtree"

	def checkLogin(self):
		pass

	def closeDB(self):
		self.log.info( "Closing DB...",)
		self.conn.close()
		self.log.info( "done")


	def process_tree_elements(self, elements, cum_path="/mango"):
		ret = []

		for element in elements:
			if element['type'] == "report":
				continue
			elif element['type'] == 'directory':
				item_path = os.path.join(cum_path, element['name'])
				ret.extend(self.process_tree_elements(element['contents'], item_path))
			elif element['type'] == 'file':
				item_path = os.path.join(cum_path, element['name'])

				# Parse out the series name if we're in a directory we understand,
				# otherwise just assume the dir name is the series.
				match = re.search(r'/Novels/([^/]+)/', item_path)
				if match:
					sname = match.group(1)
				else:
					sname = os.path.split(cum_path)[-1]

				ret.append((sname, item_path))
			else:
				self.log.error("Unknown element type: '%s'", element)

		return ret

	def loadRemoteItems(self):
		treedata = self.wg.getJson(self.tree_api)
		assert 'contents' in treedata
		assert treedata['name'] == 'mango'
		assert treedata['type'] == 'directory'
		data_unfiltered = self.process_tree_elements(treedata['contents'])

		data = []
		for sName, filen in data_unfiltered:
			if not any([filen.startswith(prefix) for prefix in MASK_PATHS]):
				assert filen.startswith(STRIP_PREFIX)
				filen = filen[len(STRIP_PREFIX):]
				sName = nt.getCanonicalMangaUpdatesName(sName)
				data.append((sName, filen))

		return data




	def getMainItems(self):
		# for item in items:
		# 	self.log.info( item)
		#

		# Muck about in the webget internal settings
		self.wg.errorOutCount = 4
		self.wg.retryDelay    = 5

		self.log.info( "Loading Madokami Main Feed")

		items = self.loadRemoteItems()
		self.processLinksIntoDB(items)




	def processLinksIntoDB(self, linksDicts, isPicked=False):


		# item["date"]     = time.time()
		# item["dlName"]   = linkName
		# item["dlLink"]   = itemUrl
		# item["baseName"] = dirName

		self.log.info( "Inserting...",)
		newItems   = 0
		oldItems   = 0
		movedItems = 0
		brokeItems = 0
		for seriesName, fqFileN in linksDicts:

			dlLink = urllib.parse.urljoin(self.url_base, fqFileN)
			fileN = os.path.split(fqFileN)[-1]


			# Look up by URL, so we don't break the UNIQUE constraint.
			rows = self.getRowsByValue(sourceUrl  = dlLink)

			if not rows:
				#We only look at the filename/series tuple to determine uniqueness,
				rows = self.getRowsByValue(originName = fileN, seriesname = seriesName)

			if len(rows) == 0:
				newItems += 1

				# Flags has to be an empty string, because the DB is annoying.
				# TL;DR, comparing with LIKE in a column that has NULLs in it is somewhat broken.
				self.insertIntoDb(retreivalTime = time.time(),
									sourceUrl   = dlLink,
									originName  = fileN,
									dlState     = 0,
									seriesName  = seriesName,
									flags       = '',
									commit      = False)  # Defer commiting changes to speed things up



				self.log.info("New item! Have canon name: %s, URL: %s, Series: %s, FileName: %s", nt.haveCanonicalMangaUpdatesName(seriesName), dlLink, seriesName, fileN)

			elif len(rows) > 1:
				brokeItems += 1
				self.log.warning("Have more then one item for filename! Wat?")
				self.log.warning("Info dict for file:")
				self.log.warning("'%s'", (dlLink, seriesName, fileN))
				self.log.warning("Found rows:")
				self.log.warning("'%s'", rows)
			elif len(rows) == 1:
				row = rows.pop()
				if row["sourceUrl"] != dlLink:
					self.log.info("File has been moved: %s!", (seriesName, fileN))
					self.log.info("Old: %s", row["sourceUrl"])
					self.log.info("New: %s", dlLink)

					self.updateDbEntryById(row["dbId"], sourceUrl = dlLink)
					movedItems += 1
				else:
					oldItems += 1

			else:
				row = row.pop()

		self.log.info( "Done")

		if newItems or movedItems:

			self.log.info( "Committing...",)
			self.conn.commit()
			self.log.info( "Committed")

		self.log.info("%s new items, %s old items, %s moved items,  %s items with broken rows.", newItems, oldItems, movedItems, brokeItems)


		# return newItems


	def go(self):

		self.resetStuckItems()
		self.log.info("Getting feed items")

		feedItems = self.getMainItems()
		# self.log.info("Processing feed Items")

		# self.processLinksIntoDB(feedItems)
		self.log.info("Complete")




class Runner(ScrapePlugins.RunBase.ScraperBase):
	loggerPath = "Main.Manga.MkL.Run"

	pluginName = "MkFLoader"


	def _go(self):

		self.log.info("Checking Mk feeds for updates")
		fl = FeedLoader()
		fl.go()
		fl.closeDB()

if __name__ == "__main__":
	import utilities.testBase as tb

	with tb.testSetup(startObservers=False):

		run = FeedLoader()
		# run.go()
		run.getMainItems()

