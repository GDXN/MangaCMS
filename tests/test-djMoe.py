

import runStatus
runStatus.preloadDicts = False

import logSetup
if __name__ == "__main__":
	logSetup.initLogging()


from ScrapePlugins.H.DjMoeLoader.Retag import Runner as TagRunner
from ScrapePlugins.H.DjMoeLoader.Run import Runner
from ScrapePlugins.H.DjMoeLoader.djMoeDbLoader import DjMoeDbLoader
from ScrapePlugins.H.DjMoeLoader.djMoeContentLoader import DjMoeContentLoader
# import DjMoeLoader.Run

import logging
import nameTools as nt

import signal
import runStatus

def signal_handler(dummy_signal, dummy_frame):
	if runStatus.run:
		runStatus.run = False
		print("Telling threads to stop")
	else:
		print("Multiple keyboard interrupts. Raising")
		raise KeyboardInterrupt


def test():

	signal.signal(signal.SIGINT, signal_handler)

	# cl = DjMoeDbLoader()
	# cl.go()
	# runner = Runner()
	# print(runner)
	# # runner.go()

	runner = TagRunner()
	print(runner)
	runner.go()

	# dbLoader = DjMoeContentLoader()
	# rows = dbLoader.retreiveTodoLinksFromDB()
	# for row in rows:
	# 	print(row)

	#nt.dirNameProxy.stop()



if __name__ == "__main__":
	test()
