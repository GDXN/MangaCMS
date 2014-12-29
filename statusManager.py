
import psycopg2
import settings


# Manage the small table used to track plugin run state.

def getConn():
	'''
	Try to get a local connection to the postgres DB. If that fails, try a IP connection. Will raise
	an exception if the IP connection cannot be made.

	Returns a psycopg2 connection on success.
	'''
	try:
		con = psycopg2.connect(dbname  = settings.DATABASE_DB_NAME,
								user    = settings.DATABASE_USER,
								password= settings.DATABASE_PASS)
	except:
		con = psycopg2.connect(host    = settings.DATABASE_IP,
								dbname  = settings.DATABASE_DB_NAME,
								user    = settings.DATABASE_USER,
								password= settings.DATABASE_PASS)
	return con

def checkStatusTableExists():
	'''
	Verify that the pluginstatus table exists. Creates it if required. This *must* be run before any plugins, or
	the plugin RunBase will fail with an exception.
	'''

	con = getConn()
	cur = con.cursor()

	cur.execute('''CREATE TABLE IF NOT EXISTS pluginStatus (name        text,
														running     boolean,
														lastRun     double precision,
														lastRunTime double precision,
														lastError   double precision DEFAULT 0,
														PRIMARY KEY(name))''')

	con.commit()
	con.close()


def getStatus(cur, pluginName):
	cur.execute("""SELECT running,lastRun,lastRunTime,lastError FROM pluginstatus WHERE name=%s""", (pluginName, ))
	rets = cur.fetchall()
	return rets


def resetAllRunningFlags():
	'''
	clear the runstate for all the plugins in the status table. Helpful for when
	plugins crash without properly clearing their runstate.
	'''

	checkStatusTableExists()
	print("Resetting run state for all plugins!")
	con = getConn()
	cur = con.cursor()
	cur.execute('''UPDATE pluginstatus SET running=false;''')
	con.commit()
	con.close()


