
import webFunctions
import settings
import os
import os.path

import nameTools as nt

import time

import urllib.parse

import runStatus
import traceback
import concurrent.futures

import ScrapePlugins.RetreivalDbBase

class MtContentLoader(ScrapePlugins.RetreivalDbBase.ScraperDbBase):


	wg = webFunctions.WebGetRobust()
	loggerPath = "Main.Mt.Cl"
	pluginName = "MangaTraders Content Retreiver"
	tableName = "MangaItems"
	dbName = settings.dbName
	urlBase = "http://www.mangatraders.com/"

	def retreiveTodoLinksFromDB(self):

		self.log.info( "Fetching items from db...",)

		rows = self.getRowsByValueDl(dlState=0)

		self.log.info( "Done")
		if not rows:
			return

		items = []
		for item in rows:
			#self.log.info( "Row = ", row)

			#self.log.info( item)
			item["retreivalTime"] = time.gmtime(item["retreivalTime"])


			baseNameLower = nt.sanitizeString(item["seriesName"])
			safeBaseName = nt.makeFilenameSafe(item["seriesName"])



			if baseNameLower in nt.dirNameProxy:
				self.log.info( "Have target dir for '%s' Dir = '%s'", baseNameLower, nt.dirNameProxy[baseNameLower]['fqPath'])
				item["targetDir"] = nt.dirNameProxy[baseNameLower]["fqPath"]
			else:
				self.log.info( "Don't have target dir for: %s Using default for: %s, full name = %s", baseNameLower, item["seriesName"], item["originName"])
				if "picked" in item["flags"]:
					targetDir = os.path.join(settings.mtSettings["dirs"]['mnDir'], safeBaseName)
				else:
					targetDir = os.path.join(settings.mtSettings["dirs"]['mDlDir'], safeBaseName)
				if not os.path.exists(targetDir):
					try:
						os.makedirs(targetDir)
						item["targetDir"] = targetDir
						self.updateDbEntry(item["sourceUrl"],flags=" ".join([item["flags"], "newdir"]))
						self.conn.commit()

						self.conn.commit()
					except OSError:
						self.log.critical("Directory creation failed?")
						self.log.critical(traceback.format_exc())
				else:
					self.log.error("Directory not found in dir-dict, but it exists!")
					item["targetDir"] = targetDir

					self.updateDbEntry(item["sourceUrl"],flags=" ".join([item["flags"], "haddir"]))
					self.conn.commit()


			items.append(item)
		self.log.info( "Have %s new items to retreive in MtDownloader" % len(items))
		#for item in items:
		#	self.log.info( item)

		#cur.execute('INSERT INTO links VALUES(?, ?, ?, ?, ?, ?, ?);',(time.asctime(link["retreivalTime"]), 0, 0, link["dlName"], link["dlLink"], link["seriesName"], link["targetDir"]))


		return items

	def getLinkFile(self, linkDict):
		pgctnt, pghandle = self.wg.getpage(linkDict["sourceUrl"], returnMultiple = True)
		pageUrl = pghandle.geturl()
		hName = urllib.parse.urlparse(pageUrl)[2].split("/")[-1]
		self.log.info( "HName: %s", hName, )
		self.log.info( "Size = %s", len(pgctnt))


		return pgctnt, hName


	def getLink(self, link):
		sourceUrl, originFileName = link["sourceUrl"], link["originName"]

		self.log.info( "Should retreive: %s", originFileName)
		self.updateDbEntry(sourceUrl, dlState=1)

		self.conn.commit()
		try:
			content, hName = self.getLinkFile(link)
		except:
			self.log.error("Unrecoverable error retreiving content %s", link)
			self.log.error("Traceback: %s", traceback.format_exc())

			self.updateDbEntry(sourceUrl, dlState=-1)
			return

		# print("Content type = ", type(content))

		fName = "%s - %s" % (originFileName, hName)
		fName = nt.makeFilenameSafe(fName)

		fqFName = os.path.join(link["targetDir"], fName)
		self.log.info( "SaveName = %s", fqFName)

		loop = 1
		while os.path.exists(fqFName):
			fName = "%s - (%d) - %s" % (originFileName, loop,  hName)
			fqFName = os.path.join(link["targetDir"], fName)
			loop += 1
		self.log.info( "Writing file")

		filePath, fileName = os.path.split(fqFName)

		try:
			with open(fqFName, "wb") as fp:
				fp.write(content)
		except TypeError:
			self.log.error("Failure trying to retreive content from source %s", sourceUrl)
			self.updateDbEntry(sourceUrl, dlState=-1, downloadPath=filePath, fileName=fileName)
			return
		#self.log.info( filePath)
		self.log.info( "Done")

		self.updateDbEntry(sourceUrl, dlState=2, downloadPath=filePath, fileName=fileName)
		return

	def fetchLinkList(self, linkList):
		try:
			for link in linkList:

				self.getLink(link)

				if not runStatus.run:
					self.log.info( "Breaking due to exit flag being set")
					break
		except:
			print("Exception!")
			traceback.print_exc()

	def processTodoLinks(self, links):
		servers = ["dl1", "dl2", "dl3", "dl4", "dl5"]

		if links:

			lists = []
			for serverN in servers:
				lists.append([item for item in links if item["dlServer"] == serverN])

			# Fetch items with no specified source DLServer first.
			self.fetchLinkList([item for item in links if item["dlServer"] == ""])
			# self.checkLogin(wg)
			self.log.info( "Need to retreive %d items" % len(links))
			with concurrent.futures.ThreadPoolExecutor(max_workers=6) as exe:

				# print("Lists = ", lists)
				rets = []
				for servList in lists:
					ret = exe.submit(self.fetchLinkList, servList)
					rets.append(ret)

				self.log.info("Executor looping while tasks execute")
				while any([item.running() for item in rets]):
					time.sleep(1)
			self.log.info("Executor exiting? Runstatus = %s", runStatus.run)
				#break
		#self.checkLogin(wg)

	# Only used by MT loader. Is a horrible hack
	# You got DB in my plugin!
	def getRowsByValueDl(self, **kwargs):
		if len(kwargs) != 1:
			raise ValueError("getRowsByValue only supports calling with a single kwarg", kwargs)
		validCols = ["dbId", "sourceUrl", "dlState"]
		key, val = kwargs.popitem()
		if key not in validCols:
			raise ValueError("Invalid column query: %s" % key)

		cur = self.conn.cursor()

		query = '''SELECT dbId,
							dlState,
							sourceUrl,
							retreivalTime,
							lastUpdate,
							sourceId,
							seriesName,
							fileName,
							originName,
							downloadPath,
							flags,
							tags,
							note,
							dlServer
							FROM {tableN} WHERE {key}=?;'''.format(tableN=self.tableName, key=key)
		# print("Query = ", query)
		ret = cur.execute(query, (val, ))

		rets = ret.fetchall()
		retL = []
		for row in rets:

			keys = ["dbId", "dlState", "sourceUrl", "retreivalTime", "lastUpdate", "sourceId", "seriesName", "fileName", "originName", "downloadPath", "flags", "tags", "note", "dlServer"]
			retL.append(dict(zip(keys, row)))
		return retL





	def go(self):
		# HAAACK
		# OVerride column names because *just* the MT table has an extra column
		self.validKwargs  =         ["mtList", "mtName", "mtId", "mtTags", "buName", "buId", "buTags", "buGenre", "buList", "readingProgress", "availProgress", "rating", "lastChanged", "lastChecked", "dlServer", "itemAdded"]
		self.validColName = ["dbId", "mtList", "mtName", "mtId", "mtTags", "buName", "buId", "buTags", "buGenre", "buList", "readingProgress", "availProgress", "rating", "lastChanged", "lastChecked", "dlServer", "itemAdded"]



		todo = self.retreiveTodoLinksFromDB()
		if not runStatus.run:
			return
		self.processTodoLinks(todo)
