
from . import absImport
import settings
import UniversalArchiveReader
import os
import logging


import runStatus

# Checks an archive (`archPath`) against the contents of the database
# accessible via the `settings.dedupApiFile` python file, which
# uses the absolute-import tool in the current directory.

# check() returns True if the archive contains any unique items,
# false if it does not.

# deleteArch() deletes the archive which has path archPath,
# and also does the necessary database manipulation to reflect the fact that
# the archive has been deleted.

def hamming(a, b, bits=64):
	x = (a ^ b)
	tot = 0
	while x:
		tot += x & 1
		x >>= 1
	return tot

class BkHammingNode(object):
	def __init__(self, nodeHash, nodeData):
		self.nodeHash = nodeHash
		self.nodeData = set((nodeData, ))
		self.children = {}

	def insert(self, nodeHash, nodeData):
		if nodeHash == self.nodeHash:
			self.nodeData.add(nodeData)
			return True

		distance = hamming(self.nodeHash, nodeHash)
		if not distance in self.children:
			self.children[distance] = [BkHammingNode(nodeHash, nodeData)]
		else:
			self.children[distance].append(BkHammingNode(nodeHash, nodeData))

	def getWithinDistance(self, baseHash, distance):
		selfDist = hamming(self.nodeHash, baseHash)

		if selfDist > distance:
			ret = set()
		else:
			ret = set(self.nodeData)


		relevantChildren = [key for key in self.children.keys() if key <= selfDist+distance and key >= selfDist-distance]
		for key in relevantChildren:

			for child in self.children[key]:
				ret |= child.getWithinDistance(baseHash, distance)

		return ret

class BkHammingTree(object):
	root = None

	def __init__(self):
		pass

	def insert(self, nodeHash, nodeData):
		if not self.root:
			self.root = BkHammingNode(nodeHash, nodeData)
		else:
			self.root.insert(nodeHash, nodeData)
	def getDistance(self, baseHash, distance):
		if not self.root:
			return set()

		return self.root.getWithinDistance(baseHash, distance)

class HamDb(object):
	def __init__(self):
		dbModule         = absImport.absImport(settings.dedupApiFile)

		self.db = dbModule.DbApi()
		self.log = logging.getLogger("Main.Deduper")

		self.log.info("Hamming Database opened.")

		self.hashTree = BkHammingTree()

	def loadPHashes(self):
		self.log.info("Loading PHashes")
		rowsIter = self.db.getPHashes()
		self.log.info("Queried. Reading results")

		rowNum = 0
		self.testHashes = []
		for row in rowsIter:
			rowNum += 1
			dbId, pHash = row
			pHash = int(pHash, 2)

			if rowNum % 1000 == 0:
				self.testHashes.append(pHash)

			if rowNum % 10000 == 0:
				self.log.info("Loading: On row %s, id = %s, hash = %s", rowNum, dbId, str(pHash).zfill(20))

				if not runStatus.run:
					self.log.info("Breaking due to exit flag being set")
					return
			self.hashTree.insert(pHash, dbId)

		self.log.info("All rows loaded! Total rows = %s", rowNum)


	def test(self):
		from timeit import Timer
		import random
		random.seed()

		testVals = []

		runs = 20
		print("Running tests")

		for x in range(10):

			t = Timer(lambda: self.hashTree.getDistance(random.choice(self.testHashes), 1))
			print(t.timeit(number=runs)/runs)


