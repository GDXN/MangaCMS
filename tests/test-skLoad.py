
import logSetup
if __name__ == "__main__":
	logSetup.initLogging()



import runStatus
from ScrapePlugins.M.SkBaseManager.Run import Runner
from ScrapePlugins.M.SkLoader.skFeedLoader import SkFeedLoader
from ScrapePlugins.M.SkLoader.skContentLoader import SkContentLoader
import signal

import os.path

def customHandler(signum, stackframe):
	if runStatus.run:
		runStatus.run = False
		print("Telling threads to stop")
	else:
		print("Multiple keyboard interrupts. Raising")
		raise KeyboardInterrupt

def test():


	cl = SkContentLoader()

	cur = cl.conn.cursor()
	ret = cur.execute("SELECT dbId, downloadPath, fileName FROM SkMangaItems WHERE downloadPath IS NOT NULL;")


	for dbId, pathTo, fileName in ret.fetchall():
		pathTo = os.path.join(pathTo, fileName)
		if os.path.exists(pathTo):
			print("Exists = ", pathTo)
		else:
			print(dbId, "Not exist = ", pathTo)
			cl.deleteRowsByValue(dbId=dbId)

	cl.closeDB()

	signal.signal(signal.SIGINT, customHandler)

	runner = Runner()

	runner.go()

	# loader = SkFeedLoader()
	# print("Running")

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

	# # getter = SkContentLoader()
	# # print(getter)



	# todo = cl.retreiveTodoLinksFromDB()

	# print("todo:", todo)
	# if not runStatus.run:
	# 	return

	# cl.processTodoLinks(todo)


	# loader.closeDB()



if __name__ == "__main__":
	try:
		test()
	finally:
		import nameTools as nt
		nt.dirNameProxy.stop()

