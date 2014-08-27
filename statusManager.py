
import psycopg2
import settings


def checkStatusTableExists():
	con = psycopg2.connect(dbname=settings.DATABASE_DB_NAME, user=settings.DATABASE_USER,password=settings.DATABASE_PASS)
	cur = con.cursor()
	cur.execute('''CREATE TABLE IF NOT EXISTS pluginstatus (name text, running boolean, lastRun real, lastRunTime real, PRIMARY KEY(name))''')
	con.commit()
	con.close()


def checkInitStatusTable(pluginName):

	con = psycopg2.connect(dbname=settings.DATABASE_DB_NAME, user=settings.DATABASE_USER,password=settings.DATABASE_PASS)
	cur = con.cursor()
	cur.execute('''INSERT INTO pluginstatus (name, running, lastRun, lastRunTime) VALUES (%s, %s, %s, %s)''', (pluginName, False, -1, -1))
	cur.commit()
	con.close()

def getStatus(cur, pluginName):
	cur.execute("""SELECT running,lastRun,lastRunTime FROM pluginstatus WHERE name=%s""", (pluginName, ))
	rets = cur.fetchall()
	return rets

def setStatus(pluginName, running=None, lastRun=None, lastRunTime=None):

	con = psycopg2.connect(dbname=settings.DATABASE_DB_NAME, user=settings.DATABASE_USER,password=settings.DATABASE_PASS)
	cur = con.cursor()
	if running != None:  # Note: Can be set to "False". This is valid!
		cur.execute('''UPDATE pluginstatus SET running=%s WHERE name=%s;''', (running, pluginName))
	if lastRun != None:
		cur.execute('''UPDATE pluginstatus SET lastRun=%s WHERE name=%s;''', (lastRun, pluginName))
	if lastRunTime != None:
		cur.execute('''UPDATE pluginstatus SET lastRunTime=%s WHERE name=%s;''', (lastRunTime, pluginName))

	con.commit()
	con.close()

