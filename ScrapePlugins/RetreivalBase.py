
import time
import ScrapePlugins.DbBase
import abc
import runStatus
import traceback
import os.path
from concurrent.futures import ThreadPoolExecutor
import ScrapePlugins.RetreivalDbBase

class ScraperBase(ScrapePlugins.RetreivalDbBase.ScraperDbBase):

	# Abstract class (must be subclassed)
	__metaclass__ = abc.ABCMeta


	itemLimit = False
	retreivalThreads = 1

	@abc.abstractmethod
	def getLink(self, link):
		pass

	# Provision for a delay. If checkDelay returns false, item is not enqueued
	def checkDelay(self, inTime):
		return True

	def retreiveTodoLinksFromDB(self):

		self.log.info( "Fetching items from db...",)

		rows = self.getRowsByValue(dlState=0)

		self.log.info( "Done")
		if not rows:
			return

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


	def fetchLinkList(self, linkList):
		try:
			for link in linkList:
				if link is None:
					self.log.error("One of the items in the link-list is none! Wat?")
					continue

				self.getLink(link)


				if not runStatus.run:
					self.log.info( "Breaking due to exit flag being set")
					break
		except KeyboardInterrupt:
			self.log.critical("Keyboard Interrupt!")
			self.log.critical(traceback.format_exc())

			# Reset the download, since failing because a keyboard interrupt is not a remote issue.
			self.updateDbEntry(link["sourceUrl"], dlState=0)
			raise

		except:
			self.log.critical("Exception!")
			traceback.print_exc()
			self.log.critical(traceback.format_exc())


	def processTodoLinks(self, links):
		if links:

			def iter_baskets_from(items, maxbaskets=3):
				'''generates evenly balanced baskets from indexable iterable'''
				item_count = len(items)
				baskets = min(item_count, maxbaskets)
				for x_i in range(baskets):
					yield [items[y_i] for y_i in range(x_i, item_count, baskets)]

			linkLists = iter_baskets_from(links, maxbaskets=self.retreivalThreads)

			with ThreadPoolExecutor(max_workers=self.retreivalThreads) as executor:

				for linkList in linkLists:
					executor.submit(self.fetchLinkList, linkList)

				executor.shutdown(wait=True)


	def insertCountIfFilenameExists(self, fqFName):

		base, ext = os.path.splitext(fqFName)
		loop = 1
		while os.path.exists(fqFName):
			fqFName = "%s - (%d).%s" % (base, loop, ext)
			loop += 1

		return fqFName



	def go(self):

		todo = self.retreiveTodoLinksFromDB()
		if not runStatus.run:
			return
		self.processTodoLinks(todo)
