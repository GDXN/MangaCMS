


import runStatus
runStatus.preloadDicts = False


import sqlalchemy as sa
import sqlalchemy.engine.url as saurl
import sqlalchemy.orm as saorm
import settings
import abc


import logging
import threading
import os
import traceback

import nameTools


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
	fspath   = sa.Column(sa.String)


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
				self.log.info("New session for thread '%s'", threadName)
				self.dbSessions[threadName] = self.sessionFactory()

			return self.dbSessions[threadName]


		else:
			return object.__getattribute__(self, name)


	def getFilenameFromIdName(self, rowid, filename):
		if not os.path.exists(settings.bookCachePath):
			self.log.warn("Cache directory for book items did not exist. Creating")
			self.log.warn("Directory at path '%s'", settings.bookCachePath)
			os.makedirs(settings.bookCachePath)

		# one new directory per 1000 items.
		dirName = '%s' % (rowid // 1000)
		dirPath = os.path.join(settings.bookCachePath, dirName)
		if not os.path.exists(dirPath):
			os.mkdir(dirPath)

		filename = 'ID%s - %s' % (rowid, filename)
		filename = nameTools.makeFilenameSafe(filename)
		fqpath = os.path.join(dirPath, filename)

		return fqpath

	def saveFile(self, url, mimetype, fileName, content):


		row = self.session.query(self.rowClass) \
					.filter_by(url=url).first()

		print("row", row)
		if row:
			if fileName in row.fspath and len(content) == int(row.contents) and mimetype == row.mimetype:
				self.log.info("Item has not changed. Skipping.")
				return
			else:
				self.log.info("Item has changed! Deleting row!")
				self.session.delete(row)

				# You have to commit for the delete to show up anywhere, because stupid?
				self.session.commit()

		newRow = self.rowClass(url=url, series=None, contents=len(content), istext=False, mimetype=mimetype, fspath='')
		self.session.add(newRow)
		self.session.commit()


		fqPath = self.getFilenameFromIdName(newRow.rowid, fileName)
		newRow.fspath = fqPath

		with open(fqPath, "wb") as fp:
			fp.write(content)

		self.session.commit()

	def printSchema(self):
		ret = Base.metadata.create_all(self.engine)
		print(ret)