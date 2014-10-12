
from . import absImport
import settings
import logging
import runStatus
import sys
sys.setrecursionlimit(1500)

from libc.stdint cimport uint64_t

cdef uint64_t hamming(uint64_t a, uint64_t b):

	cdef uint64_t x
	cdef int tot

	tot = 0

	x = (a ^ b)
	while x > 0:
		tot += x & 1
		x >>= 1
	return tot

cdef class BkHammingNode(object):

	cdef uint64_t nodeHash
	cdef set nodeData
	cdef dict children

	def __init__(self, nodeHash, nodeData):
		self.nodeData = set((nodeData, ))
		self.children = {}
		self.nodeHash = nodeHash

	cpdef insert(self, uint64_t nodeHash, nodeData):
		if nodeHash == self.nodeHash:
			self.nodeData.add(nodeData)
			return


		distance = hamming(self.nodeHash, nodeHash)
		if not distance in self.children:
			self.children[distance] = BkHammingNode(nodeHash, nodeData)
		else:
			self.children[distance].insert(nodeHash, nodeData)

	cpdef getWithinDistance(self, uint64_t baseHash, int distance):
		cdef uint64_t selfDist

		selfDist = hamming(self.nodeHash, baseHash)

		ret = set()

		if selfDist <= distance:
			ret |= set(self.nodeData)

		touched = 1

		for key in self.children.keys():

			if key <= selfDist+distance and key >= selfDist-distance:

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

		ret, touched = self.root.getWithinDistance(baseHash, distance)
		# print("Touched %s tree nodes, or %1.3f%%" % (touched, touched/self.nodes * 100))
		# print("Discovered %s match(es)" % len(ret))
		return ret
