
import time
import abc
import runStatus
import traceback
import os.path
import settings
from concurrent.futures import ThreadPoolExecutor
import ScrapePlugins.MangaScraperDbBase
import nameTools as nt

class RetreivalBase(ScrapePlugins.MangaScraperDbBase.MangaScraperDbBase):

	# Abstract class (must be subclassed)
	__metaclass__ = abc.ABCMeta


	itemLimit = False
	retreivalThreads = 1

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)


	@abc.abstractmethod
	def getLink(self, link):
		pass

	# Provision for a delay. If checkDelay returns false, item is not enqueued
	def checkDelay(self, inTime):
		return True

	# And for logging in (if needed)
	def setup(self):
		pass

	def retreiveTodoLinksFromDB(self):

		# self.QUERY_DEBUG = True

		self.log.info( "Fetching items from db...",)

		rows = self.getRowsByValue(dlState=0)

		self.log.info( "Done")

		items = []
		for item in rows:

			if self.checkDelay(item["retreivalTime"]):
				item["retreivalTime"] = time.gmtime(item["retreivalTime"])
				items.append(item)

		self.log.info( "Have %s new items to retreive in %sDownloader", len(items), self.tableKey.title())



		items = sorted(items, key=lambda k: k["retreivalTime"], reverse=True)
		if self.itemLimit:
			items = items[:self.itemLimit]

		return items


	def fetchLink(self, link):
		try:
			if link is None:
				self.log.error("Worker received null task! Wat?")
				return

			ret = self.getLink(link)
			if ret == "Limited":
				self.log.info("Remote site is rate limiting. Exiting early.")
				return

			self.mon_con.send('fetched_items.count', 1)

			if not runStatus.run:
				self.log.info( "Breaking due to exit flag being set")
				return

		except KeyboardInterrupt:
			self.log.critical("Keyboard Interrupt!")
			self.log.critical(traceback.format_exc())

			# Reset the download, since failing because a keyboard interrupt is not a remote issue.
			self.updateDbEntry(link["sourceUrl"], dlState=0)
			raise

		except Exception:
			self.mon_con.send('failed_items.count', 1)

			self.log.critical("Exception!")
			traceback.print_exc()
			self.log.critical(traceback.format_exc())



	def processTodoLinks(self, links):
		if links:

			with ThreadPoolExecutor(max_workers=self.retreivalThreads) as executor:

				for link in links:
					executor.submit(self.fetchLink, link)

				executor.shutdown(wait=True)




	# ---------------------------------------------------------------------------------------------------------------------------------------------------------
	# Filesystem stuff
	# ---------------------------------------------------------------------------------------------------------------------------------------------------------


	# either locate or create a directory for `seriesName`.
	# If the directory cannot be found, one will be created.
	# Returns {pathToDirectory string}, {HadToCreateDirectory bool}
	def locateOrCreateDirectoryForSeries(self, seriesName):

		if self.shouldCanonize:
			canonSeriesName = nt.getCanonicalMangaUpdatesName(seriesName)
		else:
			canonSeriesName = seriesName

		safeBaseName = nt.makeFilenameSafe(canonSeriesName)


		if canonSeriesName in nt.dirNameProxy:
			self.log.info("Have target dir for '%s' Dir = '%s'", canonSeriesName, nt.dirNameProxy[canonSeriesName]['fqPath'])
			return nt.dirNameProxy[canonSeriesName]["fqPath"], False
		else:
			self.log.info("Don't have target dir for: %s, full name = %s", canonSeriesName, seriesName)
			targetDir = os.path.join(settings.baseDir, safeBaseName)
			if not os.path.exists(targetDir):
				try:
					os.makedirs(targetDir)
					return targetDir, True

				except FileExistsError:
					# Probably means the directory was concurrently created by another thread in the background?
					self.log.critical("Directory doesn't exist, and yet it does?")
					self.log.critical(traceback.format_exc())
					pass
				except OSError:
					self.log.critical("Directory creation failed?")
					self.log.critical(traceback.format_exc())

			else:
				self.log.warning("Directory not found in dir-dict, but it exists!")
				self.log.warning("Directory-Path: %s", targetDir)
				self.log.warning("Base series name: %s", seriesName)
				self.log.warning("Canonized series name: %s", canonSeriesName)
				self.log.warning("Safe canonized name: %s", safeBaseName)
			return targetDir, False

	def insertCountIfFilenameExists(self, fqFName):

		base, ext = os.path.splitext(fqFName)
		loop = 1
		while os.path.exists(fqFName):
			fqFName = "%s - (%d).%s" % (base, loop, ext)
			loop += 1

		return fqFName

	def do_fetch_content(self):
		if hasattr(self, 'setup'):
			self.setup()

		todo = self.retreiveTodoLinksFromDB()
		if not runStatus.run:
			return
		if todo:
			self.processTodoLinks(todo)
		self.log.info("ContentRetreiver for %s has finished.", self.pluginName)


