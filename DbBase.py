
import traceback
import abc
from contextlib import contextmanager
import LogBase
import threading
import dbPool

# Minimal class to handle opening a DB interface.
class DbBase(LogBase.LoggerMixin, metaclass=abc.ABCMeta):

	# Abstract class (must be subclassed)
	__metaclass__ = abc.ABCMeta

	@abc.abstractmethod
	def loggerPath(self):
		return None

	def __init__(self):
		self.log.info("Base DB Interface Starting!")
		self.connections = {}

	def __del__(self):
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
			raise ValueError("Double-instantiating thread interface?")

		self.connections[tid] = dbPool.pool.getconn()
		return self.connections[tid].cursor()

	def __freeConn(self):
		conn = self.connections.popitem(threading.get_ident())
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
