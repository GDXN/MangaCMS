


import runStatus
runStatus.preloadDicts = False


import sqlalchemy as sa
import sqlalchemy.engine.url as saurl
import sqlalchemy.orm as saorm

import settings
import abc
import threading
import urllib.parse


import logging
import threading
import os
import traceback
import bs4

import nameTools


class ItemRow(object):


	__tablename__ = 'book_items'

	@abc.abstractproperty
	def _source_key(self):
		pass

	rowid    = sa.Column(sa.Integer, sa.Sequence('book_page_id_seq'), primary_key=True)
	src      = sa.Column(sa.String,  nullable=False, index=True, default=_source_key)
	dlstate  = sa.Column(sa.Integer, nullable=False, index=True, default=0)
	url      = sa.Column(sa.String,  nullable=False, unique=True, index=True)
	title    = sa.Column(sa.String)
	series   = sa.Column(sa.String)
	contents = sa.Column(sa.String)
	istext   = sa.Column(sa.Boolean, index=True, nullable=False, default=True)
	mimetype = sa.Column(sa.String)
	fspath   = sa.Column(sa.String, default='')

	@classmethod
	def getColums(self):
		# What a fucking mess.
		return list(self.__table__.columns._data.keys())


# This seems to be a funky global state tracking mechanism in SQLAlchemy
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base(cls=ItemRow)


class RowExistsException(Exception):
	pass


class TextScraper(object):



	validKwargs = ["rowid",
					"src",
					"dlstate",
					"url",
					"title",
					"series",
					"contents",
					"istext",
					"mimetype",
					"fspath"]


	@abc.abstractproperty
	def pluginName(self):
		pass

	@abc.abstractproperty
	def loggerPath(self):
		pass

	@abc.abstractproperty
	def rowClass(self):
		pass

	def __init__(self):
		self.log.info("Tsuki startup")

		# I have to wrap the DB in locks, since two pages may return
		# identical links at the same time.
		# Using transactions could result in collisions, so we lock.
		# Most of the time is spent in processing pages anyways
		self.dbLock = threading.Lock()


		engine_conf = saurl.URL(drivername='postgresql',
								host     = settings.DATABASE_IP,
								username = settings.DATABASE_USER,
								password = settings.DATABASE_PASS,
								database = settings.DATABASE_DB_NAME
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


	# ------------------------------------------------------------------------------------------------------------------
	#                      DB Interfacing stuff
	# ------------------------------------------------------------------------------------------------------------------


	def upsert(self, pgUrl, **kwargs):
		try:
			self.addPage(pgUrl, **kwargs)
		except RowExistsException:
			if kwargs:
				self.updatePage(pgUrl, **kwargs)


	def addPage(self, pgUrl, **kwargs):
		for key in kwargs:
			if not key in self.validKwargs:
				raise ValueError("Invalid key to insert into dict! '%s'" % key)

		haveRow = self.session.query(self.rowClass).filter_by(url=pgUrl).first()
		if not haveRow:

			insertArgs = {"url": pgUrl}

			for key, value in kwargs.items():
				insertArgs[key] = value

			newRow = self.rowClass(**insertArgs)
			self.session.add(newRow)
		else:
			raise RowExistsException("Doing duplicate insert?")
		self.session.commit()


	def updatePage(self, pgUrl, **kwargs):
		for key in kwargs:
			if not key in self.validKwargs:
				raise ValueError("Invalid key to insert into dict! '%s'" % key)




		result = self.session.query(self.rowClass).filter_by(url=pgUrl)
		result.one()

		insertArgs = {}

		for key, value in kwargs.items():
			insertArgs[key] = value

		result.update(insertArgs)

		self.session.commit()



	def saveFile(self, url, mimetype, fileName, content):



		# print("Begin savefile")
		row = self.session.query(self.rowClass) \
					.filter_by(url=url).first()

		if row:
			if fileName in row.fspath and len(content) == int(row.contents) and mimetype == row.mimetype:
				self.log.info("Item has not changed. Skipping.")

				return
			else:
				self.log.info("Item has changed! Deleting row!")
				self.session.delete(row)

				# You have to commit for the delete to show up anywhere, because stupid?
				self.session.commit()

		newRowDict = {  "url":url,
						"dlstate":2,
						"series":None,
						"contents":len(content),
						"istext":False,
						"mimetype":mimetype,
						"fspath":'' }

		newRow = self.rowClass(**newRowDict)
		self.session.add(newRow)

		# rowid isn't populated until commit()
		self.session.commit()

		fqPath = self.getFilenameFromIdName(newRow.rowid, fileName)
		newRow.fspath = fqPath

		self.session.commit()

		# print("Begin savefile")


		with open(fqPath, "wb") as fp:
			fp.write(content)

	def printSchema(self):
		ret = Base.metadata.create_all(self.engine)
		print(ret)

	def getToDo(self):

		# Retreiving todo items must be atomic, so we lock for that.
		with self.dbLock:
			row = self.session.query(self.rowClass)              \
						.filter_by(dlstate=0)                    \
						.order_by(sa.asc(self.rowClass.istext))  \
						.first()
			if not row:
				return False
			else:
				row.dlstate = 1
				self.session.commit()
				return row

	# ------------------------------------------------------------------------------------------------------------------
	#                      Web Scraping stuff
	# ------------------------------------------------------------------------------------------------------------------


	def getItem(self, itemUrl):

		content, handle = self.wg.getpage(itemUrl, returnMultiple=True)
		if not content or not handle:
			raise ValueError("Failed to retreive image from page '%s'!" % itemUrl)

		fileN = urllib.parse.unquote(urllib.parse.urlparse(handle.geturl())[2].split("/")[-1])
		fileN = bs4.UnicodeDammit(fileN).unicode_markup
		mType = handle.info()['Content-Type']

		# If there is an encoding in the content-type (or any other info), strip it out.
		# We don't care about the encoding, since WebFunctions will already have handled that,
		# and returned a decoded unicode object.
		if ";" in mType:
			mType = mType.split(";")[0].strip()

		self.log.info("Retreived file of type '%s', name of '%s' with a size of %0.3f K", mType, fileN, len(content)/1000.0)
		return content, fileN, mType


	def convertToReaderUrl(self, inUrl):
		url = urllib.parse.urljoin(self.baseUrl, inUrl)
		url = '/books/render?url=%s' % urllib.parse.quote(url)
		return url



	def extractLinks(self, pageCtnt):
		soup = bs4.BeautifulSoup(pageCtnt)

		for link in soup.find_all("a"):

			# Skip empty anchor tags
			try:
				turl = link["href"]
			except KeyError:
				continue

			url = urllib.parse.urljoin(self.baseUrl, turl)

			# Filter by domain
			if not self.baseUrl in url:
				continue

			# and by blocked words
			hadbad = False
			for badword in self.badwords:
				if badword in url:
					hadbad = True
			if hadbad:
				continue

			# upsert for `url`. Reset dlstate if needed
			self.upsert(url, dlstate=0)



		for imtag in soup.find_all("img"):
						# Skip empty anchor tags
			try:
				turl = imtag["src"]
			except KeyError:
				continue

			# Skip tags with `img src=""`.
			# No idea why they're there, but they are
			if not url:
				continue

			url = urllib.parse.urljoin(self.baseUrl, turl)

			# Filter by domain
			if not self.baseUrl in url:
				continue

			# and by blocked words
			hadbad = False
			for badword in self.badwords:
				if badword in url:
					hadbad = True
			if hadbad:
				continue

			# upsert for `url`. Do not reset dlstate to avoid re-transferring binary files.
			self.upsert(url, istext=False)



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
