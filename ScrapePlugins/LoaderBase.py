
if __name__ == "__main__":
	import runStatus
	runStatus.preloadDicts = False

import logging
import psycopg2
import functools
import operator as opclass
import abc

import threading
import settings
import os
import traceback

import nameTools as nt
import DbBase

import sql
import time
import sql.operators as sqlo

import ScrapePlugins.MangaScraperDbBase


class LoaderBase(ScrapePlugins.MangaScraperDbBase.MangaScraperDbBase):

	def setup(self):
		pass

	def _processLinksIntoDB(self, linksDicts):

		self.log.info( "Inserting...",)


		newItems = 0
		for link in linksDicts:
			if link is None:
				print("linksDicts", linksDicts)
				print("WAT")
				continue

			row = self.getRowsByValue(sourceUrl=link["sourceUrl"], limitByKey=False)

			if not row:
				newItems += 1

				if not "dlState" in link:
					link['dlState'] = 0

				# Patch series name.
				if 'seriesName' in link and self.shouldCanonize:
					link["seriesName"] = nt.getCanonicalMangaUpdatesName(link["seriesName"])


				self.insertIntoDb(**link)


				self.log.info("New item: %s", link)


		if self.mon_con:
			self.mon_con.incr('new_links', newItems)

		self.log.info( "Done (%s new items)", newItems)

		return newItems



	def do_fetch_feeds(self, *args, **kwargs):
		self._resetStuckItems()
		# dat = self.getFeed(list(range(50)))
		self.setup()
		dat = self.getFeed(*args, **kwargs)
		new = self._processLinksIntoDB(dat)

		# for x in range(10):
		# 	dat = self.getFeed(pageOverride=x)
		# 	self.processLinksIntoDB(dat)
