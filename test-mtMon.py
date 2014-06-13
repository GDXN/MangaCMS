
import logSetup
if __name__ == "__main__":
	logSetup.initLogging()

import nameTools as nt

import runStatus
from ScrapePlugins.MtMonitor.Run import Runner
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

	runner = Runner()
	try:
		runner.go()

	finally:
		nt.dirNameProxy.stop()

if __name__ == "__main__":
	test()
