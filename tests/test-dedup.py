
import logSetup
if __name__ == "__main__":
	logSetup.initLogging()

import archCleaner

import runStatus

import deduplicator.hamDb as hamDb

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

	hint = hamDb.HamDb()

	hint.loadPHashes()
	hint.test()


if __name__ == "__main__":

	signal.signal(signal.SIGINT, customHandler)
	try:
		test()
	finally:
		import nameTools as nt
		nt.dirNameProxy.stop()

