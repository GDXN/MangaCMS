


def selectNameLut(lut, name):
	if name in lut:
		ret = lut[name]
	else:
		ret = None


import timeit
def test():

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

CREATE INDEX muNameList_manes_index ON muNameList(fsSafeName, name);




if __name__ == "__main__":
	test()
