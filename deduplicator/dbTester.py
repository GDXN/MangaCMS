
import copy
import random

print("Installing cython")
import pyximport
pyximport.install()
print("Compiling cython files")
import deduplicator.cyHamDb as hamDb
print("Cython files loaded")

TEST_SIZE = 10000

def buildData():
	ret = []
	for x in range(TEST_SIZE):
		ret.append((random.getrandbits(64), x))
	return ret

def test():
	dat = buildData()
	# print(dat)
	hashTree = hamDb.BkHammingTree()

	for nodeHash, nodeData in dat:
		hashTree.insert(nodeHash, nodeData)

	# for nodeData, nodeHash in dat:
	# 	hashTree.insert(nodeHash, nodeData+TEST_SIZE)






	# for node in hashTree:
	# 	print("Node", node)
	moves = []

	for x in range(30):
		item = random.choice(dat)
		dat.remove(item)
		tgtHash, tgtId = item
		# print(tgtId, tgtHash)
		ret, moved = hashTree.remove(tgtHash, tgtId)
		moves.append(moved)
		if ret != 1:
			print("What?", ret)


	dat2 = list(hashTree)
	dat.sort()
	dat2.sort()


	for x in range(len(dat)):
		if dat[x] != dat2[x]:
			print("Match error!", dat[x], dat2[x])

	return sum(moves) / len(moves)

def testBase():

	moves = []
	for x in range(1000):
		moves.append(test())
		if x % 25 == 0:
			print("Loop", x)
			print("Running average moves", sum(moves) / len(moves))

if __name__ == "__main__":
	import utilities.testBase
	with utilities.testBase.testSetup():
		testBase()

