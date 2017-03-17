

import logging
import settings
import psycopg2
import runStatus
import time
import traceback
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
		self.checkStatusTableExists()

	def checkStatusTableExists(self):
		con = psycopg2.connect(host=settings.DATABASE_IP, dbname=settings.DATABASE_DB_NAME, user=settings.DATABASE_USER,password=settings.DATABASE_PASS)
		with con.cursor() as cur:

			cur.execute("SELECT relname FROM pg_class;")
			haveItems = cur.fetchall()
			haveItems = [index[0] for index in haveItems]
			if not "pluginstatus" in haveItems:
				raise ValueError("PluginStatus table does not exist. Has MainScrape never been run?")

			print(self.pluginName)

			cur.execute('''SELECT name FROM pluginStatus WHERE name=%s''', (self.pluginName,))
			ret = cur.fetchall()
			if not ret:
				cur.execute('''INSERT INTO pluginStatus (name, running, lastRun, lastRunTime) VALUES (%s, %s, %s, %s)''', (self.pluginName, False, -1, -1))
				con.commit()

		con.close()

	def amRunning(self):

		con = psycopg2.connect(host=settings.DATABASE_IP, dbname=settings.DATABASE_DB_NAME, user=settings.DATABASE_USER,password=settings.DATABASE_PASS)
		with con.cursor() as cur:
			cur.execute("""SELECT running FROM pluginStatus WHERE name=%s""", (self.pluginName, ))
			rets = cur.fetchone()[0]
		self.log.info("%s is running = '%s', as bool = '%s'", self.pluginName, rets, bool(rets))
		return rets

	def setStatus(self, pluginName=None, running=None, lastRun=None, lastRunTime=None):
		if pluginName == None:
			pluginName=self.pluginName

		con = psycopg2.connect(host=settings.DATABASE_IP, dbname=settings.DATABASE_DB_NAME, user=settings.DATABASE_USER,password=settings.DATABASE_PASS)
		with con.cursor() as cur:
			if running != None:  # Note: Can be set to "False". This is valid!
				cur.execute('''UPDATE pluginStatus SET running=%s WHERE name=%s;''', (running, pluginName))
			if lastRun != None:
				cur.execute('''UPDATE pluginStatus SET lastRun=%s WHERE name=%s;''', (lastRun, pluginName))
			if lastRunTime != None:
				cur.execute('''UPDATE pluginStatus SET lastRunTime=%s WHERE name=%s;''', (lastRunTime, pluginName))

		con.commit()
		con.close()

	def setError(self, errTime):

		con = psycopg2.connect(host=settings.DATABASE_IP, dbname=settings.DATABASE_DB_NAME, user=settings.DATABASE_USER,password=settings.DATABASE_PASS)
		with con.cursor() as cur:
			cur.execute('''UPDATE pluginStatus SET lastError=%s WHERE name=%s;''', (errTime, self.pluginName))

		con.commit()
		con.close()


	def go(self):
		if self.amRunning():
			self.log.critical("%s is already running! Not launching again!", self.pluginName)
			return
		else:
			self.log.info("%s Started.", self.pluginName)

			runStart = time.time()
			self.setStatus(running=True, lastRun=runStart)
			try:
				self._go()
			except Exception:
				# If we have a uncaught exception in the plugin, log the exception traceback (which will get logged to
				# the DB), and then re-raise
				self.setError(errTime=time.time())
				self.log.critical("Uncaught major exception in plugin!")
				self.log.critical("Traceback:")
				for line in traceback.format_exc().split("\n"):
					self.log.critical(line)

				raise

			finally:
				self.setStatus(running=False, lastRunTime=time.time()-runStart)
				self.log.info("%s finished.", self.pluginName)




	def _go(self):

		self.log.info("Checking %s feeds for updates", self.sourceName)
		fl = self.feedLoader()
		fl.do_fetch_feeds()

		time.sleep(3)
		#print "wat", cl

		if not runStatus.run:
			return

		cl = self.contentLoader()
		todo = cl.do_fetch_content()
