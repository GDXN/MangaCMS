

import logging
import settings
import psycopg2
import runStatus
import time
import abc


class ScraperBase(metaclass=abc.ABCMeta):

	# Abstract class (must be subclassed)
	__metaclass__ = abc.ABCMeta



	@abc.abstractmethod
	def pluginName(self):
		return None

	@abc.abstractmethod
	def loggerPath(self):
		return None


	def __init__(self):
		self.log = logging.getLogger(self.loggerPath)
		self.log.info("Loading %s Runner", self.pluginName)
		self.checkInitStatusTable()

	def checkInitStatusTable(self):
		con = psycopg2.connect(host=settings.PSQL_IP, dbname=settings.DATABASE_DB_NAME, user=settings.DATABASE_USER,password=settings.DATABASE_PASS)
		with con.cursor() as cur:
			cur.execute('''CREATE TABLE IF NOT EXISTS pluginStatus (name text,
																	running boolean,
																	lastRun double precision,
																	lastRunTime double precision,
																	PRIMARY KEY(name))''')
			print(self.pluginName)

			cur.execute('''SELECT name FROM pluginStatus WHERE name=%s''', (self.pluginName,))
			ret = cur.fetchall()
			if not ret:
				cur.execute('''INSERT INTO pluginStatus (name, running, lastRun, lastRunTime) VALUES (%s, %s, %s, %s)''', (self.pluginName, False, -1, -1))
				con.commit()

		con.close()

	def amRunning(self):

		con = psycopg2.connect(host=settings.PSQL_IP, dbname=settings.DATABASE_DB_NAME, user=settings.DATABASE_USER,password=settings.DATABASE_PASS)
		with con.cursor() as cur:
			cur.execute("""SELECT running FROM pluginStatus WHERE name=%s""", (self.pluginName, ))
			rets = cur.fetchone()[0]
		self.log.info("%s is running = '%s', as bool = '%s'", self.pluginName, rets, bool(rets))
		return rets

	def setStatus(self, pluginName=None, running=None, lastRun=None, lastRunTime=None):
		if pluginName == None:
			pluginName=self.pluginName

		con = psycopg2.connect(host=settings.PSQL_IP, dbname=settings.DATABASE_DB_NAME, user=settings.DATABASE_USER,password=settings.DATABASE_PASS)
		with con.cursor() as cur:
			if running != None:  # Note: Can be set to "False". This is valid!
				cur.execute('''UPDATE pluginStatus SET running=%s WHERE name=%s;''', (running, pluginName))
			if lastRun != None:
				cur.execute('''UPDATE pluginStatus SET lastRun=%s WHERE name=%s;''', (lastRun, pluginName))
			if lastRunTime != None:
				cur.execute('''UPDATE pluginStatus SET lastRunTime=%s WHERE name=%s;''', (lastRunTime, pluginName))

		con.commit()
		con.close()


	def go(self):
		if self.amRunning():
			self.log.critical("%s is already running! Not launching again!", self.pluginName)
			return
		else:
			self.log.info("%s Started.", self.pluginName)

			runStart = time.time()
			self.setStatus(self.pluginName, running=True, lastRun=runStart)
			try:
				self._go()
			finally:
				self.setStatus(self.pluginName, running=False, lastRunTime=time.time()-runStart)
				self.log.info("%s finished.", self.pluginName)




	def _go(self):

		self.log.info("Checking %s feeds for updates", self.sourceName)
		fl = self.feedLoader()
		fl.go()
		fl.closeDB()

		time.sleep(3)
		#print "wat", cl

		if not runStatus.run:
			return

		cl = self.contentLoader()
		todo = cl.go()
		cl.closeDB()
