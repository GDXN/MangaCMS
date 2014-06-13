
import sqlite3
import settings
def unzipRet(retIn):

	retL = []
	if retIn:
		keys = ["dbId", "mtName", "mtId", "mtTags", "mtList", "buName", "buId", "buTags", "buList", "readingProgress", "availProgress", "rating", "lastChanged"]
		for ret in retIn:
			retL.append(dict(zip(keys, ret)))
	return retL

def printDb(conn):
	cur = conn.cursor()


	ret = cur.execute('SELECT * FROM MangaSeries WHERE mtName="7 Billion Needles" or buName="7 Billion Needles";')
	ret = unzipRet(ret.fetchall())
	if ret:
		ret = ret[0]
		keys = list(ret.keys())
		keys.sort()
		for key in keys:
			keyStr = "{key}".format(key=key)
			print("	", keyStr, " "*(20-len(keyStr)), ret[key])
	print("----------")
	ret = cur.execute('SELECT * FROM MangaSeries WHERE mtName="70 Oku no Hari" or buName="70 Oku no Hari";')
	ret = unzipRet(ret.fetchall())
	if ret:
		ret = ret[0]
		keys = list(ret.keys())
		keys.sort()
		for key in keys:
			keyStr = "{key}".format(key=key)
			print("	", keyStr, " "*(20-len(keyStr)), ret[key])



def test():
	sql = sqlite3.connect('links.db')
	print("Settings=", settings.dbName)
	# settings.dbName = '/media/Storage/Scripts/MTDlTool/linksTest.db'
	print("Settings=", settings.dbName)

	import DbManagement.MonitorTool
	tool = DbManagement.MonitorTool.Inserter()
	print(tool)
	print(tool.dbName)

	printDb(sql)
	tool.mergeItems({"mtName":"7 Billion Needles"}, {"buName":"70 Oku no Hari"})
	tool.closeDB()

if __name__ == "__main__":
	test()

