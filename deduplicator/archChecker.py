

import UniversalArchiveInterface
import os
import os.path
import logging
import rpyc
import magic
import shutil

import hashlib

PHASH_DISTANCE_THRESHOLD = 2


class ArchChecker(object):

	def __init__(self, archPath, phashDistance=PHASH_DISTANCE_THRESHOLD, pathFilter=None):
		self.log = logging.getLogger("Main.Deduper")

		self.remote = rpyc.connect("localhost", 12345)

		if not pathFilter:
			pathFilter = ['']
		# pathFilter filters
		# Basically, if you pass a list of valid path prefixes, any matches not
		# on any of those path prefixes are not matched.
		# Default is [''], which matches every path, because "anything".startswith('') is true
		self.maskedPaths = pathFilter
		self.pdist = phashDistance
		self.log.info("ArchChecker Instantiated")

		self.arch = archPath

	def process(self, moveToPath=None):
		self.log.info("Processing download '%s'", self.arch)
		status, bestMatch, intersections = self.remote.root.processDownload(self.arch, pathFilter=self.maskedPaths, distance=self.pdist, moveToPath=moveToPath)
		self.log.info("Processed archive. Return status '%s'", status)
		if bestMatch:
			self.log.info("Matching archive '%s'", bestMatch)
		return status, bestMatch, intersections
