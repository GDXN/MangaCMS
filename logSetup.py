

import logging
import colorama as clr

import os.path
import sys
import time
import traceback
# Pylint can't figure out what's in the record library for some reason
#pylint: disable-msg=E1101

colours = [clr.Fore.BLUE, clr.Fore.RED, clr.Fore.GREEN, clr.Fore.YELLOW, clr.Fore.MAGENTA, clr.Fore.CYAN, clr.Back.YELLOW + clr.Fore.BLACK, clr.Back.YELLOW + clr.Fore.BLUE, clr.Fore.WHITE]

def getColor(idx):
	return colours[idx%len(colours)]


class DatabaseHandler(logging.Handler):


	def __init__(self, level=logging.DEBUG):
		logging.Handler.__init__(self, level)

		import settings
		import psycopg2

		try:
			self.conn = psycopg2.connect(dbname=settings.DATABASE_DB_NAME, user=settings.DATABASE_USER,password=settings.DATABASE_PASS)
		except psycopg2.OperationalError:
			self.conn = psycopg2.connect(host=settings.DATABASE_IP, dbname=settings.DATABASE_DB_NAME, user=settings.DATABASE_USER,password=settings.DATABASE_PASS)

		self.checkInitDb()

	def checkInitDb(self):
		with self.conn.cursor() as cur:

			cur.execute('''CREATE TABLE IF NOT EXISTS logTable (
												dbid      SERIAL PRIMARY KEY,
												time      DOUBLE PRECISION NOT NULL,
												source    TEXT NOT NULL,
												level     INTEGER,
												content   TEXT);''')


			cur.execute("SELECT relname FROM pg_class;")
			haveIndexes = cur.fetchall()
			haveIndexes = [index[0] for index in haveIndexes]



			indexes = [
				# ("logTable_dbid_index",       '''CREATE INDEX logTable ON logTable (dbid   );'''  ),  # Primary key gets an index automatically
				("logTable_time_index",       '''CREATE INDEX logTable_time_index       ON logTable (time   );'''  ),
				("logTable_source_index",     '''CREATE INDEX logTable_source_index     ON logTable (source );'''  ),
				("logTable_istext_index",     '''CREATE INDEX logTable_istext_index     ON logTable (level  );'''  ),
				("logTable_title_coll_index", '''CREATE INDEX logTable_title_coll_index ON logTable USING BTREE (source COLLATE "en_US" text_pattern_ops);'''  )
			]

			for name, createCall in indexes:
				if not name.lower() in haveIndexes:
					cur.execute(createCall)




	def emit(self, record):

		name    = record.name
		logTime = record.created
		level   = record.levelno
		msg     = record.getMessage()
		values  = (name, logTime, level, msg)

		with self.conn.cursor() as cur:
			cur.execute("BEGIN;")
			cur.execute("INSERT INTO logTable (source, time, level, content) VALUES (%s, %s, %s, %s);", values)
			cur.execute("COMMIT;")





class ColourHandler(logging.Handler):

	def __init__(self, level=logging.DEBUG):
		logging.Handler.__init__(self, level)
		self.formatter = logging.Formatter('\r%(name)s%(padding)s - %(style)s%(levelname)s - %(message)s'+clr.Style.RESET_ALL)
		clr.init()

		self.logPaths = {}

	def emit(self, record):

		# print record.levelname
		# print record.name

		segments = record.name.split(".")
		if segments[0] == "Main" and len(segments) > 1:
			segments.pop(0)
			segments[0] = "Main."+segments[0]

		nameList = []

		for indice, pathSegment in enumerate(segments):
			if not indice in self.logPaths:
				self.logPaths[indice] = [pathSegment]
			elif not pathSegment in self.logPaths[indice]:
				self.logPaths[indice].append(pathSegment)

			name = clr.Style.RESET_ALL
			name += getColor(self.logPaths[indice].index(pathSegment))
			name += pathSegment
			name += clr.Style.RESET_ALL
			nameList.append(name)


		record.name = ".".join(nameList)

		if record.levelname == "DEBUG":
			record.style = clr.Style.DIM
		elif record.levelname == "WARNING":
			record.style = clr.Style.BRIGHT
		elif record.levelname == "ERROR":
			record.style = clr.Style.BRIGHT+clr.Fore.RED
		elif record.levelname == "CRITICAL":
			record.style = clr.Style.BRIGHT+clr.Back.BLUE+clr.Fore.RED
		else:
			record.style = clr.Style.NORMAL

		record.padding = ""
		print((self.format(record)))

class RobustFileHandler(logging.FileHandler):
	"""
	A handler class which writes formatted logging records to disk files.
	"""

	def emit(self, record):
		"""
		Emit a record.

		If the stream was not opened because 'delay' was specified in the
		constructor, open it before calling the superclass's emit.
		"""
		failures = 0
		while self.stream is None:
			try:
				self.stream = self._open()
			except:

				time.sleep(1)
				if failures > 3:
					traceback.print_exc()
					print("Cannot open log file?")
					return
				failures += 1
		failures = 0
		while failures < 3:
			try:
				logging.StreamHandler.emit(self, record)
				break
			except:
				failures += 1
		else:
			traceback.print_stack()
			print("Error writing to file?")


		self.close()


def exceptHook(exc_type, exc_value, exc_traceback):
	if issubclass(exc_type, KeyboardInterrupt):
		sys.__excepthook__(exc_type, exc_value, exc_traceback)
		return
	mainLogger = logging.getLogger("Main")			# Main logger
	mainLogger.critical('Uncaught exception!')
	mainLogger.critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

# Global hackyness to detect and warn on double-initialization of the logging systems.
LOGGING_INITIALIZED = False

def initLogging(logLevel=logging.INFO, logToDb=True):

	global LOGGING_INITIALIZED
	if LOGGING_INITIALIZED:
		current_stack = traceback.format_stack()
		print("ERROR - Logging initialized twice!")
		for line in current_stack:
			print(line.rstrip())
		return

	LOGGING_INITIALIZED = True

	print("Setting up loggers....")

	if not os.path.exists(os.path.join("./logs")):
		os.mkdir(os.path.join("./logs"))

	mainLogger = logging.getLogger("Main")			# Main logger
	mainLogger.setLevel(logLevel)

	# Do not propigate up to any parent loggers other things install
	mainLogger.propagate = False

	# You have to add the dbLogger first, because the colorHandler logger
	# modifies the internal values of the record.name attribute,
	# and if the dbLogger is added after it, the modified values
	# are also sent to the db logger.
	if logToDb:
		try:
			dbLog = DatabaseHandler()
			mainLogger.addHandler(dbLog)
		except:
			print("Warning! Failed to instantiate database logging interface!")
			traceback.print_exc()


	ch = ColourHandler()
	mainLogger.addHandler(ch)

	logName	= "Error - %s.txt" % (time.strftime("%Y-%m-%d %H;%M;%S", time.gmtime()))

	errLogHandler = RobustFileHandler(os.path.join("./logs", logName))
	errLogHandler.setLevel(logging.WARNING)
	formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
	errLogHandler.setFormatter(formatter)

	mainLogger.addHandler(errLogHandler)

	# Install override for excepthook, to catch all errors
	sys.excepthook = exceptHook

	print("done")


if __name__ == "__main__":
	initLogging(logToDb=True)
	log = logging.getLogger("Main.Test")
	log.debug("Testing logging - level: debug")
	log.info("Testing logging - level: info")
	log.warn("Testing logging - level: warn")
	log.error("Testing logging - level: error")
	log.critical("Testing logging - level: critical")
