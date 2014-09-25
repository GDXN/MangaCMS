
import logSetup
if __name__ == "__main__":
	logSetup.initLogging()


import runStatus
runStatus.preloadDicts = False

from ScrapePlugins.LoneMangaLoader.Run import Runner
from ScrapePlugins.LoneMangaLoader.LmContentLoader import LmContentLoader

import signal
import time
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


	# nt.dirNameProxy.startDirObservers()

	# runner = LmContentLoader()

	runner = Runner()
	runner.go()
	# todo = runner.retreiveTodoLinksFromDB()
	# for row in todo:
	# 	print("todo", row)
	# pages = runner.getImageUrls('http://lonemanga.com/manga/gun/2')
	# for page in pages.items():
	# 	print(page)



	# runner = Runner()
	# runner.go()




if __name__ == "__main__":

	signal.signal(signal.SIGINT, customHandler)
	try:
		test()
	finally:
		import nameTools as nt
		nt.dirNameProxy.stop()

