
# This seems to be a funky global state tracking mechanism in SQLAlchemy
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()



import sqlalchemy as sa
import sqlalchemy.engine.url as saurl
import sqlalchemy.orm as saorm
import settings
import abc


import logging
import threading
import os
import traceback


class PageRow(object):

	@abc.abstractmethod
	def __tablename__(self):
		pass

	rowid    = sa.Column(sa.Integer, sa.Sequence('ts_page_id_seq'), primary_key=True)
	url      = sa.Column(sa.String, nullable=False, unique=True)
	title    = sa.Column(sa.String)
	series   = sa.Column(sa.String)
	contents = sa.Column(sa.String)

	# This requires inheriting from Base, which has to be done in the subclasses
	@classmethod
	def getColums(self):
		# What a fucking mess.
		return list(self.__table__.columns._data.keys())

	def __repr__(self):
		return "<title(rowId='%s', url='%s', name='%s', contents='%s', series='%s')>" % (self.rowid, self.url, self.title, self.contents, self.series)

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
		engine_conf = saurl.URL(drivername='postgresql',
								username = settings.DATABASE_USER,
								password = settings.DATABASE_PASS,
								database = settings.DATABASE_DB_NAME
								# host = settings.DATABASE_IP,
								)

		self.engine = sa.create_engine(engine_conf, echo=True)
		self.sessionFactory = saorm.sessionmaker(bind=self.engine)
		self.session = self.sessionFactory()


		self.log = logging.getLogger(self.loggerPath)

		self.loggers = {}
		self.dbSessions = {}
		self.lastLoggerIndex = 1

		self.log.info("Loading %s Runner BaseClass", self.pluginName)

		self.columns = self.rowClass.getColums()
		print("Columns", self.columns)

	# More hackiness to make sessions intrinsically thread-safe.
	def __getattribute__(self, name):

		threadName = threading.current_thread().name
		if name == "log" and "Thread-" in threadName:
			if threadName not in self.loggers:
				self.loggers[threadName] = logging.getLogger("Main.%s.Thread-%d" % (self.loggerPath, self.lastLoggerIndex))
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