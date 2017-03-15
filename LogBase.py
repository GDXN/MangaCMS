
import logging
import threading
import abc

class LoggerMixin(metaclass=abc.ABCMeta):

	@abc.abstractproperty
	def loggerPath(self):
		pass

	def __init__(self):
		self.loggers = {}
		self.lastLoggerIndex = 1


	def __getattribute__(self, name):

		threadName = threading.current_thread().name
		if name == "log" and "Thread-" in threadName:
			if threadName not in self.loggers:
				self.loggers[threadName] = logging.getLogger("%s.Thread-%d" % (self.loggerPath, self.lastLoggerIndex))
				self.lastLoggerIndex += 1
			return self.loggers[threadName]


		else:
			return super().__getattribute__(name)

	@property
	def log(self):

		threadName = threading.current_thread().name
		if "Thread-" in threadName:
			if threadName not in self.loggers:
				self.loggers[threadName] = logging.getLogger("%s.Thread-%d" % (self.loggerPath, self.lastLoggerIndex))
				self.lastLoggerIndex += 1

		# If we're not called in the context of a thread, just return the base log-path
		else:
			self.loggers[threadName] = logging.getLogger("%s" % (self.loggerPath,))
		return self.loggers[threadName]


class TestClass(LoggerMixin):
	loggerPath = 'Main.Wat'

	def test(self):
		self.log.info("Wat?")



if __name__ == "__main__":
	print("Test mode!")
	import logSetup
	logSetup.initLogging()


	scraper = TestClass()
	print(scraper)
	extr = scraper.test()
	# print(extr['fLinks'])

