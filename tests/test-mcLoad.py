
import logSetup
if __name__ == "__main__":
	logSetup.initLogging()



import runStatus

from ScrapePlugins.McLoader.mcFeedLoader import McFeedLoader
from ScrapePlugins.McLoader.mcContentLoader import McContentLoader
import signal

import nameTools as nt

import os.path

def customHandler(signum, stackframe):
	if runStatus.run:
		runStatus.run = False
		print("Telling threads to stop")
	else:
		print("Multiple keyboard interrupts. Raising")
		raise KeyboardInterrupt

def test():



	loader = McFeedLoader()
	loader.go()
	# feedItems = loader.getAllItems()
	# feedItems = loader.getItemPages("http://mngacow.com/50-Million-Km/")
	loader.log.info("Processing feed Items")

	# loader.processLinksIntoDB(feedItems)


	# cl = McContentLoader()
	# cl.go()


	# cl.getContainerPages('http://www.batoto.net/read/_/257032/for-alice_ch0.5_by_misty-rain-scans/1')
	# cl.getContainerPages('http://www.batoto.net/read/_/257091/untouchable_ch7_by_royal-hearts/1')
	# cl.getContainerPages('http://www.batoto.net/read/_/257156/gaussian-blur_ch14--v2-_by_kawa-scans/1')

	# print(cl.extractFilename("Witch Craft Works - vol 8 ch 36 Page 1 | Batoto!"))
	# print(cl.extractFilename("For Alice - ch 0.5 | Batoto!"))
	# print(cl.extractFilename("JoJo&#39;s Bizarre Adventure Part 6: Stone Ocean - vol 65 ch 608 Page 1 | Batoto!"))
	# print(cl.extractFilename("Eighth - vol 7 ch 26 Page 1 | Batoto!"))
	# print(cl.extractFilename("Love Pop - vol 1 ch 5 Page 1 | Batoto!"))
	# print(cl.extractFilename("Omairi desu yo - vol 3 ch 8a Page 1 | Batoto!"))

	# cur = cl.conn.cursor()
	# ret = cur.execute("SELECT dbId, downloadPath, fileName FROM BtMangaItems WHERE downloadPath IS NOT NULL;")


	# for dbId, pathTo, fileName in ret.fetchall():
	# 	pathTo = os.path.join(pathTo, fileName)
	# 	if os.path.exists(pathTo):
	# 		print("Exists = ", pathTo)
	# 	else:
	# 		print(dbId, "Not exist = ", pathTo)
	# 		cl.deleteRowsByValue(dbId=dbId)

	# cl.closeDB()


	# runner = Runner()

	# runner.go()

	# loader = BtFeedLoader()
	# print("Running")
	# loader.go()

	# loader.go()

	# try:
	# 	newItems = 0
	# 	for x in range(270, 3000):
	# 		print("Loop", x)

	# 		itemTemp = loader.getMainItems(rangeOverride=1, rangeOffset=x)

	# 		# for item in itemTemp:
	# 		# 	print("Item", item)

	# 		newItems += loader.processLinksIntoDB(itemTemp, isPicked=0)

	# 		loader.log.info("Loop %s, items %s", x, newItems)

	# 	loader.log.info( "Adding items to queue")


	# finally:
	# 	nt.dirNameProxy.stop()
	# # runner.checkFeed()
	# # print("Runniner = ", runner)

	# # getter = BtContentLoader()
	# # print(getter)



	# todo = cl.retreiveTodoLinksFromDB()

	# print("todo:", todo)
	# if not runStatus.run:
	# 	return

	# cl.processTodoLinks(todo)


	# loader.closeDB()



if __name__ == "__main__":

	signal.signal(signal.SIGINT, customHandler)
	try:
		test()
	finally:
		import nameTools as nt
		nt.dirNameProxy.stop()

