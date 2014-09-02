

import psycopg2
import abc
import settings
import logging

# Absolutely minimal class to handle opening a DB interface.

class DbBase(metaclass=abc.ABCMeta):

	# Abstract class (must be subclassed)
	__metaclass__ = abc.ABCMeta

	@abc.abstractmethod
	def loggerPath(self):
		return None

	def __init__(self):
		self.log = logging.getLogger(self.loggerPath)
		self.log.info("Base DB Interface Starting!")

	def openDB(self):
		self.log.info("Opening DB...",)
		self.conn = psycopg2.connect(host=settings.PSQL_IP, dbname=settings.DATABASE_DB_NAME, user=settings.DATABASE_USER,password=settings.DATABASE_PASS)
		# self.conn.autocommit = True
		self.log.info("DB opened.")

	def closeDB(self):
		self.log.info("Closing DB...",)
		self.conn.close()
		self.log.info("DB Closed")

