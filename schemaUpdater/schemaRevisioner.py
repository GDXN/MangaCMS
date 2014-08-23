
import sqlite3
import settings
import sys

from schemaUpdater.schema001to002 import updateOne2Two
from schemaUpdater.schema002to003 import schemaTwo2Three
from schemaUpdater.schema003to004 import schemaThree2Four
from schemaUpdater.schema004to005 import schemaFour2Five
from schemaUpdater.schema005to006 import schemaFive2Six
from schemaUpdater.schema006to007 import schemaSix2Seven
from schemaUpdater.schema007to008 import update_8

from schemaUpdater.schema008to009 import update_9         # Rev 9 is the first postgres rev


from schemaUpdater.schema006to007 import doTableCounts
from schemaUpdater.schema008to009 import doTableCountsPostgre

CURRENT_SCHEMA = 9

def getSchemaRev(conn):
	cur = conn.cursor()
	cur.execute('''SELECT name FROM sqlite_master WHERE type='table';''')
	rets = cur.fetchall()
	tables = [item for sublist in rets for item in sublist]
	if len(tables) == 0:
		print("First run.")
		return -1

	if not "schemaRev" in tables:
		if "AllMangaItems" in tables:
			return 2
		else:
			return 0
	else:
		ret = cur.execute("SELECT schemaVersion FROM schemaRev;")
		rets = cur.fetchall()
		if rets and len(rets) != 1:
			print("ret = ", rets)
			raise ValueError("Schema version table should only have one row!")
		else:
			return rets.pop()[0]

def verifySchemaUpToDate():
	conn = sqlite3.connect(settings.dbName, timeout=10)
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
	conn = sqlite3.connect(settings.dbName, timeout=10)
	conn.execute('''UPDATE schemaRev SET schemaVersion=?;''', (newNum, ))
	conn.commit()


def createSchemaRevTable(conn):
	conn.execute('''CREATE TABLE IF NOT EXISTS schemaRev (schemaVersion int DEFAULT 1);''')
	conn.execute('''INSERT INTO schemaRev VALUES (1);''')
	conn.commit()

def updateDatabaseSchema(fastExit=False):
	conn = sqlite3.connect(settings.dbName, timeout=10)

	rev = getSchemaRev(conn)
	print("Current Database Schema Rev = ", rev)

	if rev == -1:
		print("Database not instantiated. Deferring DB creation to plugins.")
		return

	# Rev 0 is no schema version table at all
	if rev == 0:
		createSchemaRevTable(conn)

	# Rev 1 is identical to the pre-versioning system, only with a version table.

	rev = getSchemaRev(conn)
	if rev == 1:
		updateOne2Two(conn)
		updateSchemaRevNo(2)

	# Rev 2 amalgamates all the downloader tables into a single table.


	rev = getSchemaRev(conn)
	if rev == 2:
		schemaTwo2Three(conn)
		updateSchemaRevNo(3)

	# Rev 3 adds insert and delete triggers to track table-size


	rev = getSchemaRev(conn)
	if rev == 3:
		schemaThree2Four(conn)
		updateSchemaRevNo(4)

	# Rev 4 drops the MangaTraders table colums, since MT isn't coming back.

	rev = getSchemaRev(conn)
	if rev == 4:
		schemaFour2Five(conn)
		updateSchemaRevNo(5)

	rev = getSchemaRev(conn)
	if rev == 5:
		schemaFive2Six(conn)
		updateSchemaRevNo(6)

	rev = getSchemaRev(conn)
	if rev == 6:
		schemaSix2Seven(conn)
		updateSchemaRevNo(7)

	rev = getSchemaRev(conn)
	if rev == 7:
		update_8(conn)
		updateSchemaRevNo(8)

	rev = getSchemaRev(conn)
	if rev == 8:
		update_9(conn)
		updateSchemaRevNo(9)

	rev = getSchemaRev(conn)
	if fastExit:
		return


	if rev >= 9:
		pass
		print("FIX TABLE COUNTS FOR POSTGRE")
		# doTableCountsPostgre(conn)
	else:
		doTableCounts(conn)

	rev = getSchemaRev(conn)
	print("Current Rev = ", rev)
	print("Database structure us up to date.")

