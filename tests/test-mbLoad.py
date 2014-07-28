
import logSetup
if __name__ == "__main__":
	logSetup.initLogging()

import nameTools as nt

import runStatus
# from ScrapePlugins.MbLoader.Run import Runner
from ScrapePlugins.MbLoader.mbFeedLoader import MbFeedLoader
from ScrapePlugins.MbLoader.mbContentLoader import MbContentLoader
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

	# loader = MbFeedLoader()
	# print("Running")
	# loader.go()

	fetcher = MbContentLoader()

	links = fetcher.go()



if __name__ == "__main__":
	try:
		test()

	finally:
		nt.dirNameProxy.stop()
