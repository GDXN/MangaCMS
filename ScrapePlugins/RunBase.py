

import logging
import settings
import sqlite3
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

		con = sqlite3.connect(settings.dbName, timeout=30)
		con.execute('''CREATE TABLE IF NOT EXISTS pluginStatus (name text,
																running boolean,
																lastRun real,
																lastRunTime real,
																PRIMARY KEY(name) ON CONFLICT REPLACE)''')
		print(self.pluginName)
		con.execute('''INSERT INTO pluginStatus (name, running, lastRun, lastRunTime) VALUES (?, ?, ?, ?)''', (self.pluginName, False, -1, -1))
		con.commit()

		con.close()

	def amRunning(self):

		con = sqlite3.connect(settings.dbName, timeout=30)
		cur = con.cursor()
		ret = cur.execute("""SELECT running FROM pluginStatus WHERE name=?""", (self.pluginName, ))
		rets = ret.fetchone()[0]
		self.log.info("%s is running = '%s', as bool = '%s'", self.pluginName, rets, bool(rets))
		return rets

	def setStatus(self, pluginName=None, running=None, lastRun=None, lastRunTime=None):
		if pluginName == None:
			pluginName=self.pluginName

		con = sqlite3.connect(settings.dbName, timeout=30)
		if running != None:  # Note: Can be set to "False". This is valid!
			con.execute('''UPDATE pluginStatus SET running=? WHERE name=?;''', (running, pluginName))
		if lastRun != None:
			con.execute('''UPDATE pluginStatus SET lastRun=? WHERE name=?;''', (lastRun, pluginName))
		if lastRunTime != None:
			con.execute('''UPDATE pluginStatus SET lastRunTime=? WHERE name=?;''', (lastRunTime, pluginName))

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
			self._go()
			self.setStatus(self.pluginName, running=False, lastRunTime=time.time()-runStart)
			self.log.info("%s finished.", self.pluginName)


	@abc.abstractmethod
	def _go(self):
		pass
