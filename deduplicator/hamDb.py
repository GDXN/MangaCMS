
from . import absImport
import settings
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
			self.children[distance] = BkHammingNode(nodeHash, nodeData)
		else:
			self.children[distance].insert(nodeHash, nodeData)

	def getWithinDistance(self, baseHash, distance, isRoot=False):
		selfDist = hamming(self.nodeHash, baseHash)

		ret = set()

		if selfDist <= distance:
			ret |= set(self.nodeData)

		touched = 1

		relevantChildKey = [key for key in self.children.keys() if key <= selfDist+distance and key >= selfDist-distance]


		for key in relevantChildKey:

			new, tmpTouch = self.children[key].getWithinDistance(baseHash, distance)
			touched += tmpTouch
			ret |= new

		return ret, touched

class BkHammingTree(object):
	root = None

	def __init__(self):
		self.nodes = 0

	def insert(self, nodeHash, nodeData):
		if not self.root:
			self.root = BkHammingNode(nodeHash, nodeData)
		else:
			self.root.insert(nodeHash, nodeData)

		self.nodes += 1

	def getWithinDistance(self, baseHash, distance):
		if not self.root:
			return set()

		ret, touched = self.root.getWithinDistance(baseHash, distance, isRoot=True)
		# print("Touched %s tree nodes, or %1.3f%%" % (touched, touched/self.nodes * 100))
		# print("Discovered %s match(es)" % len(ret))
		return ret


class HamDb(object):
	def __init__(self):
		dbModule         = absImport.absImport(settings.dedupApiFile)

		self.db = dbModule.DbApi()
		self.log = logging.getLogger("Main.Deduper")

		self.log.info("Hamming Database opened.")

		self.hashTree = BkHammingTree()

	def loadPHashes(self):
		self.log.info("Loading PHashes")
		rowsIter = self.db.getPHashes(limit=200000)
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


	def doTest(self, targetHash, distance):
		items = self.hashTree.getWithinDistance(targetHash, distance)

		# print(items)

	def test(self):
		from timeit import Timer
		import random
		random.seed()

		testVals = []

		runs = 20
		print("Running tests")



		for x in range(10):

			t = Timer(lambda: (self.doTest(random.choice(self.testHashes), 2)))
			print(t.timeit(number=runs)/runs)

def test():

	hint = HamDb()

	hint.loadPHashes()
	hint.test()


if __name__ == "__main__":
	import utilities.testBase
	with utilities.testBase.testSetup():
		test()
