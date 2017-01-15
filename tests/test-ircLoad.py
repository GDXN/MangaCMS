
import logSetup
if __name__ == "__main__":
	logSetup.initLogging()


import nameTools as nt
import runStatus

from ScrapePlugins.M.IrcGrabber.FetchBot import IrcRetreivalInterface
import signal
import time


def customHandler(signum, stackframe):
	if runStatus.run:
		runStatus.run = False
		print("Telling threads to stop")
	else:
		print("Multiple keyboard interrupts. Raising")
		raise KeyboardInterrupt

def test():

	signal.signal(signal.SIGINT, customHandler)
	nt.dirNameProxy.startDirObservers()
	mgr = IrcRetreivalInterface()
	# print("mgr", mgr)

	# print(mgr.bot.db)
	# todo = mgr.bot.db.retreiveTodoLinksFromDB()
	# for row in todo:
	# 	print(row)

	mgr.startBot()

	while 1:
		if not  runStatus.run:
			break
		time.sleep(1)


	mgr.stopBot()



if __name__ == "__main__":
	try:

		test()
	finally:
		nt.dirNameProxy.stop()


