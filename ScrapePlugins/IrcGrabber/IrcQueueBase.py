


import webFunctions
import re
import json

import time

import runStatus
import settings
import pickle
import bs4


import ScrapePlugins.RetreivalDbBase

import abc

class IrcQueueBase(ScrapePlugins.RetreivalDbBase.ScraperDbBase):


	def closeDB(self):
		self.log.info( "Closing DB...",)
		self.conn.close()
		self.log.info( "done")


	@abc.abstractmethod
	def getMainItems(self, rangeOverride=None, rangeOffset=None):
		pass


	def processLinksIntoDB(self, itemDataSets, isPicked=False):

		self.log.info( "Inserting...",)
		newItems = 0
		for itemKey, itemData in itemDataSets:
			if itemData is None:
				print("itemDataSets", itemDataSets)
				print("WAT")

			row = self.getRowsByValue(limitByKey=False, sourceUrl=itemKey)
			if not row:
				newItems += 1


				# Flags has to be an empty string, because the DB is annoying.
				#
				# TL;DR, comparing with LIKE in a column that has NULLs in it is somewhat broken.
				#
				self.insertIntoDb(retreivalTime = time.time(),
									sourceUrl   = itemKey,
									sourceId    = itemData,
									dlState     = 0,
									flags       = '',
									commit=False)

				self.log.info("New item: %s", itemData)


		self.log.info( "Done")
		self.log.info( "Committing...",)
		self.conn.commit()
		self.log.info( "Committed")

		return newItems


	def go(self):

		self.resetStuckItems()
		self.log.info("Getting feed items")

		feedItems = self.getMainItems()
		self.log.info("Processing feed Items")

		self.processLinksIntoDB(feedItems)
		self.log.info("Complete")





