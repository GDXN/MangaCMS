
import psycopg2
import settings
import sys


from schemaUpdater.rowCountTracker import setupTableCountersPostgre         # Rev 9 is the first postgres rev
from schemaUpdater.rowCountTracker import doTableCountsPostgre         # Rev 9 is the first postgres rev



CURRENT_SCHEMA = 10

def getSchemaRev(conn):
	cur = conn.cursor()
	cur.execute('''SELECT tablename FROM pg_catalog.pg_tables WHERE tableowner=%s;''', (settings.DATABASE_USER, ))
	rets = cur.fetchall()
	tables = [item for sublist in rets for item in sublist]
	if len(tables) == 0:
		print("First run.")
		return -1
	print("Tables = ", tables)
	if not "schemaRev".lower() in tables:
		return -1
	else:
		cur.execute("SELECT schemaVersion FROM schemaRev;")
		rets = cur.fetchall()
		if rets and len(rets) != 1:
			print("ret = ", rets)
			raise ValueError("Schema version table should only have one row!")
		else:
			return rets.pop()[0]

def verifySchemaUpToDate():
	try:
		conn = psycopg2.connect(dbname  = settings.DATABASE_DB_NAME,
								user    = settings.DATABASE_USER,
								password= settings.DATABASE_PASS)
	except:
		conn = psycopg2.connect(host    = settings.DATABASE_IP,
								dbname  = settings.DATABASE_DB_NAME,
								user    = settings.DATABASE_USER,
								password= settings.DATABASE_PASS)

	rev = getSchemaRev(conn)
	if rev < CURRENT_SCHEMA:
		print("Database Schema is out of date! Please run the scraper to allow it to update the database structure first!")
		sys.exit(1)
	elif rev > CURRENT_SCHEMA:
		print("Schema is more recent then current? Wat?")
		sys.exit(1)

	else:
		print("Database Schema Up to date")
		return

def updateSchemaRevNo(newNum):
	try:
		conn = psycopg2.connect(dbname  = settings.DATABASE_DB_NAME,
								user    = settings.DATABASE_USER,
								password= settings.DATABASE_PASS)
	except:
		conn = psycopg2.connect(host    = settings.DATABASE_IP,
								dbname  = settings.DATABASE_DB_NAME,
								user    = settings.DATABASE_USER,
								password= settings.DATABASE_PASS)
	cur = conn.cursor()
	cur.execute('''UPDATE schemaRev SET schemaVersion=%s;''', (newNum, ))
	conn.commit()


def createSchemaRevTable(conn):

	cur = conn.cursor()
	cur.execute('''CREATE TABLE IF NOT EXISTS schemaRev (schemaVersion int DEFAULT 1);''')
	cur.execute('''INSERT INTO schemaRev VALUES (1);''')
	conn.commit()

def updateDatabaseSchema(fastExit=False):
	try:
		conn = psycopg2.connect(dbname  = settings.DATABASE_DB_NAME,
								user    = settings.DATABASE_USER,
								password= settings.DATABASE_PASS)
	except:
		conn = psycopg2.connect(host    = settings.DATABASE_IP,
								dbname  = settings.DATABASE_DB_NAME,
								user    = settings.DATABASE_USER,
								password= settings.DATABASE_PASS)

	rev = getSchemaRev(conn)
	print("Current Database Schema Rev = ", rev)

	if rev == -1:
		createSchemaRevTable(conn)
		updateSchemaRevNo(9)
	else:
		# We have to defer all this to the next run, so
		rev = getSchemaRev(conn)
		if rev == 9:
			setupTableCountersPostgre(conn)
			updateSchemaRevNo(10)

		rev = getSchemaRev(conn)

		if fastExit:
			return

		doTableCountsPostgre(conn)

		rev = getSchemaRev(conn)
		print("Current Rev = ", rev)
		print("Database structure us up to date.")

