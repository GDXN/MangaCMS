
import psycopg2
import settings

# Manage the small table used to track plugin run state. Messy, should be refactored.

# TODO: This needs to be just a existance check, not a create table call. Right now, there are two places
# this table can be created, and if one is changed and the other not, shit could get messy.
def checkStatusTableExists():

	try:
		con = psycopg2.connect(dbname  = settings.DATABASE_DB_NAME,
								user    = settings.DATABASE_USER,
								password= settings.DATABASE_PASS)
	except:
		con = psycopg2.connect(host    = settings.DATABASE_IP,
								dbname  = settings.DATABASE_DB_NAME,
								user    = settings.DATABASE_USER,
								password= settings.DATABASE_PASS)

	cur = con.cursor()
	cur.execute('''CREATE TABLE IF NOT EXISTS pluginstatus (name text, running boolean, lastRun real, lastRunTime real, PRIMARY KEY(name))''')
	con.commit()
	con.close()

def getStatus(cur, pluginName):
	cur.execute("""SELECT running,lastRun,lastRunTime FROM pluginstatus WHERE name=%s""", (pluginName, ))
	rets = cur.fetchall()
	return rets


def resetAllRunningFlags():
	checkStatusTableExists()
	print("Resetting run state for all plugins!")

	try:
		con = psycopg2.connect(dbname  = settings.DATABASE_DB_NAME,
								user    = settings.DATABASE_USER,
								password= settings.DATABASE_PASS)
	except:
		con = psycopg2.connect(host    = settings.DATABASE_IP,
								dbname  = settings.DATABASE_DB_NAME,
								user    = settings.DATABASE_USER,
								password= settings.DATABASE_PASS)
	cur = con.cursor()
	cur.execute('''UPDATE pluginstatus SET running=false;''')
	con.commit()
	con.close()


