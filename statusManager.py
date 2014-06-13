
import sqlite3
import settings


def checkStatusTableExists():
	con = sqlite3.connect(settings.dbName, timeout=30)
	con.execute('''CREATE TABLE IF NOT EXISTS pluginStatus (name text, running boolean, lastRun real, lastRunTime real, PRIMARY KEY(name) ON CONFLICT REPLACE)''')
	con.commit()
	con.close()


def checkInitStatusTable(pluginName):

	con = sqlite3.connect(settings.dbName, timeout=30)
	con.execute('''INSERT INTO pluginStatus (name, running, lastRun, lastRunTime) VALUES (?, ?, ?, ?)''', (pluginName, False, -1, -1))
	con.commit()
	con.close()

def getStatus(cur, pluginName):
	ret = cur.execute("""SELECT running,lastRun,lastRunTime FROM pluginStatus WHERE name=?""", (pluginName, ))
	rets = ret.fetchall()[0]
	return rets

def setStatus(pluginName, running=None, lastRun=None, lastRunTime=None):

	con = sqlite3.connect(settings.dbName, timeout=30)
	if running != None:  # Note: Can be set to "False". This is valid!
		con.execute('''UPDATE pluginStatus SET running=? WHERE name=?;''', (running, pluginName))
	if lastRun != None:
		con.execute('''UPDATE pluginStatus SET lastRun=? WHERE name=?;''', (lastRun, pluginName))
	if lastRunTime != None:
		con.execute('''UPDATE pluginStatus SET lastRunTime=? WHERE name=?;''', (lastRunTime, pluginName))

	con.commit()
	con.close()

