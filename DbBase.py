
import traceback
import abc
from contextlib import contextmanager
import LogBase
import threading
import dbPool
import traceback

# Minimal class to handle opening a DB interface.
class DbBase(LogBase.LoggerMixin, metaclass=abc.ABCMeta):

	# Abstract class (must be subclassed)
	__metaclass__ = abc.ABCMeta

	@abc.abstractmethod
	def loggerPath(self):
		return None

	def __init__(self):
		super().__init__()
		self.connections = {}

	def __del__(self):
		if hasattr(self, 'connections'):
			for conn in self.connections:
				dbPool.pool.putconn(conn)

	@property
	def __thread_cursor(self):
		'''
		__getCursor and __freeConn rely on "magic" thread ID cookies to associate
		threads with their correct db pool interfaces
		'''

		tid = threading.get_ident()

		if tid in self.connections:
			self.log.critical('Recursive access to singleton thread-specific resource!')
			self.log.critical("Calling thread ID: '%s'", tid)
			self.log.critical("Allocated handles")
			for key, value in self.connections.items():
				self.log.critical("	'%s', '%s'", key, value)

			raise ValueError("Recursive cursor retreival! What's going on?")

		self.connections[tid] = dbPool.pool.getconn()
		return self.connections[tid].cursor()

	def __freeConn(self):
		conn = self.connections.pop(threading.get_ident())
		dbPool.pool.putconn(conn)



	@contextmanager
	def transaction(self, commit=True):
		cursor = self.__thread_cursor
		if commit:
			cursor.execute("BEGIN;")

		try:
			yield cursor

		except Exception as e:
			self.log.error("Error in transaction!")
			self.log.error(traceback.format_exc())
			if commit:
				cursor.execute("ROLLBACK;")
			raise e

		finally:
			if commit:
				cursor.execute("COMMIT;")
			self.__freeConn()

