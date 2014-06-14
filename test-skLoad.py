
import logSetup
if __name__ == "__main__":
	logSetup.initLogging()



import runStatus
from ScrapePlugins.SkLoader.Run import Runner
from ScrapePlugins.SkLoader.skFeedLoader import SkFeedLoader
from ScrapePlugins.SkLoader.skContentLoader import SkContentLoader
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

	loader = SkFeedLoader()
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

	# # getter = SkContentLoader()
	# # print(getter)

	# cl = SkContentLoader()
	# todo = cl.retreiveTodoLinksFromDB()

	# # print("todo:", todo)
	# if not runStatus.run:
	# 	return

	# cl.processTodoLinks(todo)


	# loader.closeDB()
	# cl.closeDB()



if __name__ == "__main__":
	try:
		test()
	finally:
		import nameTools as nt
		nt.dirNameProxy.stop()

