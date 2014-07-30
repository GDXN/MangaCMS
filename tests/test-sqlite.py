
import sqlite3
import os.path

def test():

	print("Setup start")
	db = sqlite3.connect('/media/Storage/Scripts/MangaCMS/links.db', timeout=10)

	cur = db.cursor()
	ret = cur.execute('SELECT dbId, downloadPath, fileName, tags FROM MangaItems WHERE dlState=2;')

	ret = list(ret)
	missing = 0
	total = 0
	for row in ret:
		total += 1
		dbId, downloadPath, fileName, tags = row
		if tags and "was-duplicate" in tags:
			continue
		filePath = os.path.join(downloadPath, fileName)
		if not os.path.exists(filePath):
			missing += 1
			print(filePath)
			if not tags:
				tags = ""
			tags = tags.lower()
			tags = tags.split()
			tags.append("missing")
			tags = set(tags)
			tags = " ".join(tags)
			print(tags)

			cur.execute('UPDATE MangaItems SET tags=? WHERE dbId=?;', (tags, dbId))

	db.commit()


	print("Missing", missing, "Total", total)

if __name__ == "__main__":
	test()
