


def selectNameLut(lut, name):
	if name in lut:
		ret = lut[name]
	else:
		ret = None


import timeit
def test2():

	setupSql = r'''
print("Setup start")
import sqlite3
import random
random.seed('slartibartfast')
db = sqlite3.connect('/media/Storage/Scripts/MangaCMS/links.db', timeout=10)

cur = db.cursor()
ret = cur.execute('SELECT fsSafeName FROM muNameList;')
rets = ret.fetchall()
names = [item[0] for item in rets]
print("Loaded names from Db for random choice")


'''

	setupLut = r'''
print("Setup start")
from __main__ import selectNameLut
import sqlite3
import random
random.seed('slartibartfast')
db = sqlite3.connect('/media/Storage/Scripts/MangaCMS/links.db', timeout=10)

cur = db.cursor()
ret = cur.execute('SELECT fsSafeName FROM muNameList;')
rets = ret.fetchall()
names = [item[0] for item in rets]
print("Loaded names from Db for random choice")


ret = cur.execute('SELECT fsSafeName, name FROM muNameList;')
rets = ret.fetchall()

lut = {}
for fsSafe, name in rets:
	if fsSafe in lut:
		lut[fsSafe].append(name)
	else:
		lut[fsSafe] = [name]

print("LUT Built. Doing run")
'''

	iterations = 500
	print("Timing SQL Lookups")
	sqlRun = timeit.repeat('cur.execute("SELECT name FROM muNameList WHERE fsSafeName=?;", (random.choice(names), )).fetchall()', repeat=2, setup=setupSql, number=iterations)
	print("Sql run timed. Timing LUT")
	lutRun = timeit.repeat('selectNameLut(lut, random.choice(names))', repeat=2, setup=setupLut, number=iterations)
	print("sqlRun", sqlRun)
	for run in sqlRun:
		print("%.15f" % (run/iterations))
	print("lut", lutRun)
	for run in lutRun:
		print("%.15f" % (run/iterations))



def test():


	setupLut = r'''
print("Building Strings")
import random
import string
import re
strs = []
for x in range(1000):
	strs.append(''.join([random.choice(string.printable) for n in range(32)]))

print("Strings Built")

def prepFilenameForMatching(inStr):
	inStr = sanitizeString(inStr)
	inStr = makeFilenameSafe(inStr)
	return inStr.lower()

bracketStripRe = re.compile(r"(\[[\+\~\-\!\d\w:]*\])")

def removeBrackets(inStr):
	inStr = bracketStripRe.sub(" ", inStr)
	while inStr.find("  ")+1:
		inStr = inStr.replace("  ", " ")
	return inStr
# Basically used for dir-path cleaning to prep for matching, and not much else
def sanitizeString(inStr, flatten=True):
	baseName = removeBrackets(inStr)				#clean brackets

	if flatten:
		baseName = baseName.replace("~", "")		 # Spot fixes. We'll see if they break anything
		baseName = baseName.replace(".", "")
		baseName = baseName.replace(";", "")
		baseName = baseName.replace(":", "")
		baseName = baseName.replace("-", "")
		baseName = baseName.replace("?", "")
		baseName = baseName.replace("!", "")
		baseName = baseName.replace('"', "")

	# baseName = baseName.replace("'", "")
	baseName = baseName.replace("  ", " ")

	# baseName = unicodedata.normalize('NFKD', baseName).encode("ascii", errors="ignore")  # This will probably break shit


	return baseName.lower().strip()

def makeFilenameSafe(inStr):

	inStr = inStr.replace("%20", " ") \
				 .replace("<",  " ") \
				 .replace(">",  " ") \
				 .replace(":",  " ") \
				 .replace("\"", " ") \
				 .replace("/",  " ") \
				 .replace("\\", " ") \
				 .replace("|",  " ") \
				 .replace("?",  " ") \
				 .replace("*",  " ") \
				 .replace('"', " ")

	# Collapse all the repeated spaces down.
	while inStr.find("  ")+1:
		inStr = inStr.replace("  ", " ")

	inStr = inStr.rstrip(".")  # Windows file names can't end in dot. For some reason.
	inStr = inStr.strip(" ")   # And can't have leading or trailing spaces

	return inStr


	'''

	setup2 = r'''
print("Building Strings")
import random
import string
import re
strs = []
for x in range(1000):
	strs.append(''.join([random.choice(string.printable) for n in range(32)]))

print("Strings Built")

cleanerRe = re.compile(r"\[[\+\~\-\!\d\w:]*\]|[~.;:-?!\"<>\\/|*]| +")
bracketStripRe = re.compile(r"(\[[\+\~\-\!\d\w:]*\])")

def prepFilenameForMatching(inStr):

	inStr = inStr.replace("%20", " ")

	inStr = cleanerRe.sub(" ", inStr)

	while inStr.find("  ")+1:
		inStr = inStr.replace("  ", " ")

	inStr = inStr.rstrip(".")  # Windows file names can't end in dot. For some reason.
	inStr = inStr.strip(" ")   # And can't have leading or trailing spaces

	return inStr.lower()




def sanitizeString(inStr, flatten=True):


	if flatten:
		baseName = cleanerRe.sub(" ", inStr)
	else:
		baseName = bracketStripRe.sub(" ", inStr)				#clean brackets

	# baseName = baseName.replace("'", "")
	while inStr.find("  ")+1:
		inStr = inStr.replace("  ", " ")

	return baseName.lower().strip()

def makeFilenameSafe(inStr):

	inStr = inStr.replace("%20", " ")
	cleanerRe = re.compile(r"[<>:\"\\/|?*]")
	inStr = cleanerRe.sub(" ", inStr)

	# Collapse all the repeated spaces down.
	return inStr


	'''

	iterations = 50000

	lut2Run = timeit.repeat('prepFilenameForMatching(random.choice(strs))', repeat=3, setup=setup2, number=iterations)
	lutRun = timeit.repeat('prepFilenameForMatching(random.choice(strs))', repeat=3, setup=setupLut, number=iterations)

	print("lut", lutRun)
	for run in lutRun:
		print("%.15f" % (run/iterations))

	print("lut2", lutRun)
	for run in lut2Run:
		print("%.15f" % (run/iterations))


if __name__ == "__main__":
	test()
