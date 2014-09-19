



import sqlalchemy as sa
import sqlalchemy.engine.url as saurl
import sqlalchemy.orm as saorm
import settings
import abc


import logging
import threading
import os
import traceback


class ItemRow(object):


	__tablename__ = 'book_items'

	@abc.abstractmethod
	def _source_key(self):
		pass

	rowid    = sa.Column(sa.Integer, sa.Sequence('book_page_id_seq'), primary_key=True)
	src      = sa.Column(sa.String, nullable=False, index=True, default=_source_key)
	url      = sa.Column(sa.String, nullable=False, unique=True, index=True)
	title    = sa.Column(sa.String)
	series   = sa.Column(sa.String)
	contents = sa.Column(sa.String)
	istext   = sa.Column(sa.Boolean, index=True, nullable=False)
	mimetype = sa.Column(sa.String)
	fsPath   = sa.Column(sa.String)


	@classmethod
	def getColums(self):
		# What a fucking mess.
		return list(self.__table__.columns._data.keys())


# This seems to be a funky global state tracking mechanism in SQLAlchemy
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base(cls=ItemRow)



class TextScraper(object):



	@abc.abstractmethod
	def pluginName(self):
		pass

	@abc.abstractmethod
	def loggerPath(self):
		pass

	@abc.abstractmethod
	def rowClass(self):
		pass

	def __init__(self):
		self.log.info("Tsuki startup")
		engine_conf = saurl.URL(drivername='postgresql',
								username = settings.DATABASE_USER,
								password = settings.DATABASE_PASS,
								database = settings.DATABASE_DB_NAME
								# host = settings.DATABASE_IP,
								)

		self.engine = sa.create_engine(engine_conf)
		self.sessionFactory = saorm.sessionmaker(bind=self.engine)
		self.session = self.sessionFactory()


		self.loggers = {}
		self.dbSessions = {}
		self.lastLoggerIndex = 1

		self.log.info("Loading %s Runner BaseClass", self.pluginName)

		self.columns = self.rowClass.getColums()

		Base.metadata.create_all(self.engine)



	# More hackiness to make sessions intrinsically thread-safe.
	def __getattribute__(self, name):

		threadName = threading.current_thread().name
		if name == "log" and "Thread-" in threadName:
			if threadName not in self.loggers:
				self.loggers[threadName] = logging.getLogger("%s.Thread-%d" % (self.loggerPath, self.lastLoggerIndex))
				self.lastLoggerIndex += 1
			return self.loggers[threadName]


		elif name == "session":
			if threadName not in self.dbSessions:
				self.dbSessions[threadName] = self.sessionFactory()
				# self.dbSessions[threadName].autocommit = True
			return self.dbSessions[threadName]


		else:
			return object.__getattribute__(self, name)


	def printSchema(self):
		ret = Base.metadata.create_all(self.engine)
		print(ret)