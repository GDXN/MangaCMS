
from contextlib import contextmanager

@contextmanager
def testSetup(load=True):

	import runStatus
	runStatus.preloadDicts = False
	runStatus.run = True

	import logSetup
	import signal
	import nameTools as nt


	logSetup.initLogging(logToDb=True)

	def signal_handler(dummy_signal, dummy_frame):
		if runStatus.run:
			runStatus.run = False
			print("Telling threads to stop")
		else:
			print("Multiple keyboard interrupts. Raising")
			raise KeyboardInterrupt

	signal.signal(signal.SIGINT, signal_handler)

	if load:
		nt.dirNameProxy.startDirObservers()

	yield

