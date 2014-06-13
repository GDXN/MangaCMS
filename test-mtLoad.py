
import logSetup
if __name__ == "__main__":
	logSetup.initLogging()

import nameTools as nt

import runStatus
from ScrapePlugins.MtLoader.Run import Runner
from ScrapePlugins.MtLoader.mtFeedLoader import MtFeedLoader
from ScrapePlugins.MtLoader.mtContentLoader import MtContentLoader
import signal

def customHandler(signum, stackframe):
	if runStatus.run:
		runStatus.run = False
		print("Telling threads to stop")
	else:
		print("Multiple keyboard interrupts. Raising")
		raise KeyboardInterrupt

def test():

	signal.signal(signal.SIGINT, customHandler)

	# runner = Runner()
	# try:
	# 	runner.go()

	loader = MtFeedLoader()
	print("Running")

	loader.go()

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

	# # getter = MtContentLoader()
	# # print(getter)

	cl = MtContentLoader()
	todo = cl.retreiveTodoLinksFromDB()

	if not runStatus.run:
		return

	cl.processTodoLinks(todo)
	cl.closeDB()



if __name__ == "__main__":
	test()
