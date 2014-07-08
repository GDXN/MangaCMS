
import sys
if sys.version_info < ( 3, 4):
	# python too old, kill the script
	sys.exit("This script requires Python 3.4 or newer!")




# Drag in path to the library (MESSY)
import os, sys
lib_path = os.path.abspath('../')
print("Lib Path = ", lib_path)
sys.path.append(lib_path)


import logSetup
logSetup.initLogging()

import nameTools as nt

def canonify(inList):
	ret = {}
	for item in inList:
		canonName = nt.getCanonicalMangaUpdatesName(item)

		if canonName not in ret:
			ret[canonName] = [item]
		else:
			ret[canonName].append(item)
	return ret

def loadList(listName):
	ret = set()
	with open(listName, "rb") as fp:
		for line in fp.readlines():
			line = line.decode("utf-8")
			line = line.strip()
			ret.add(line)
	return ret

def loadLists():
	srcLists = ["mt-files.txt"]
	rmLists = ["Batoto-files.txt", "bakabt-files.txt"]

	sourceItems = set()
	rmItems = set()
	for listName in srcLists:
		sourceItems |= loadList(listName)
	for listName in rmLists:
		rmItems |= loadList(listName)

	print("Source items = ", len(sourceItems))
	print("Duped items = ", len(rmItems))


	sourceDict = canonify(sourceItems)
	rmDict = canonify(rmItems)

	print("Source dict = ", len(sourceDict))
	print("Duped dict = ", len(rmDict))

	multi = 0

	for key in rmDict:
		if key in sourceDict:

			if len(rmDict[key]) == 1 and len(sourceDict[key]):
				sourceDict.pop(key)
			else:

				# print("Multiple items for key?", key, rmDict[key], sourceDict[key])
				multi += 1

	print("Source dict = ", len(sourceDict))
	print("Duped dict = ", len(rmDict))
	print("Multi = ", multi)

	out = open("noMatch.txt", "w")
	for key, val in sourceDict.items():
		out.write("{have} - {key} - {val}\n".format(have=nt.haveCanonicalMangaUpdatesName(val[0]), key=key, val=val))
	out.close()

def go():
	loadLists()



if __name__ == "__main__":
	go()


