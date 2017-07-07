
def migrateDb(conn):
	cur = conn.cursor()

	import settings
	import psycopg2
	import traceback
	print("wat?")


	pgconn = psycopg2.connect(host=settings.DATABASE_IP,
							dbname  =settings.DATABASE_DB_NAME,
							user    =settings.DATABASE_USER,
							password=settings.DATABASE_PASS)
	pcur = pgconn.cursor()



	cur = conn.cursor()
	print("Conn = ", conn)


	# print("Cleaning out bad keys")
	# ret = cur.execute("SELECT DISTINCT(buId) FROM muNameList;")
	# print("Scanning")
	# for item in ret.fetchall():
	# 	dup = cur.execute("SELECT * FROM MangaSeries WHERE buId=?", (item[0], ))
	# 	dups = dup.fetchall()
	# 	if not dups:
	# 		print("Item missing primary key link!", item)
	# 		cur.execute("DELETE FROM muNameList WHERE buId=?", (item[0], ))
	# conn.commit()
	# print("All primary key constraints should now be valid.")




	schema = conn.execute("SELECT * FROM sqlite_master;").fetchall()
	schema = [item[4] for item in schema]

	rowNum = 0

	# for row in schema:
	outf = open("dump.sql", "w")

	for row in conn.iterdump():
		if row is None:
			continue


		# Create trigger statements will require considerable rework. Just ignore them for the moment.
		if "CREATE TRIGGER" in row:
			continue

		# Sqlite outputs booleans as 0/1. Postgre can apparenly only accept true/false.
		# SInce the pluginStatus table is automatically rebuilt, just ignore all rows.
		if "INTO pluginStatus" in row:
			continue


		# Postgres casts all table and colum names to lowercase.
		# Sqlite dumps them as unquoted camelcase. Therefore, we
		# re-format all create calls to properly quote table and index names.
		if "CREATE TABLE " in row:
			if not "[" and "]" in row:
				items = row.split(" ", 3)
				row = '%s %s %s %s' % (items[0], items[1], items[2], items[3])
			else:
				row = row.replace("[", ' ').replace("]", ' ')


		if "CREATE INDEX " in row:
			if not "[" and "]" in row:
				items = row.split(" ", 3)
				row = '%s %s %s %s' % (items[0], items[1], items[2], items[3])
			else:
				row = row.replace("[", ' ').replace("]", ' ')


		# Also, postgre doesn't have sqlite's nice "ON CONFLICT {xxx}" clause. I can fix this in my code,
		# But it breaks the import. Dump it.
		if "ON CONFLICT REPLACE" in row:
			row = row.replace("ON CONFLICT REPLACE", " ")

		row = row.strip()

		if row.startswith("INSERT INTO "):
			insert, into, tableName, remainder = row.split(" ", 3)
			tableName = tableName.replace('"', "")
			row = '%s %s %s %s' % (insert, into, tableName, remainder)

		# Or a lot of the other things that make sqlite nice, apparently. Arrrrgh
		row = row.replace("'NOCASE'", " ")
		row = row.replace("COLLATE", " ").replace("collate", " ")
		row = row.replace("NOCASE", " ").replace("nocase", " ")

		row = row.replace(" REAL ", " DOUBLE PRECISION ")

		# print("Row",  row)
		# outf.write(row+"\n")
		try:
			if not "INTO pluginStatus" in row:
				pcur.execute(row)
		except psycopg2.ProgrammingError:
			if "pluginStatus" in row:
				traceback.print_exc()
			else:
				raise

		rowNum += 1
		if rowNum % 1000 == 0:
			print("On row %s" % rowNum)
			print("Row '%s'" % row)
	# outf.close()

	print("Querying db contents", pcur.execute("SELECT * FROM mangaitems;"))
	print(cur.fetchall())

	conn.commit()
	pgconn.commit()


	print("Querying db contents", pcur.execute("SELECT * FROM mangaitems;"))
	print(cur.fetchall())


def update_9(conn):

	print("Migrating to Postgres DB")
	migrateDb(conn)
	print("Done!")




def doTableCountsPostgre(conn):

	doTableCount(conn, "MangaItems")
	doTableCount(conn, "HentaiItems")

def doTableCount(conn, table):


	print("Ensuring commit hooks for table-size tracking exist.")

	# Increment on creation
	conn.execute('''CREATE TRIGGER IF NOT EXISTS {tableName}Counts_CreateTrigger
										AFTER INSERT ON {tableName}
										BEGIN
											UPDATE MangaItemCounts
												SET quantity = quantity + 1
												WHERE sourceSite=NEW.sourceSite AND dlState=NEW.dlState;
										END;'''.format(tableName=table))

	# Deincrement on delete
	conn.execute('''CREATE TRIGGER IF NOT EXISTS {tableName}Counts_DeleteTrigger
										BEFORE DELETE ON {tableName}
										BEGIN
											UPDATE MangaItemCounts
												SET quantity = quantity - 1
												WHERE sourceSite=OLD.sourceSite AND dlState=OLD.dlState;
										END;'''.format(tableName=table))

	# Deincrement on delete
	conn.execute('''CREATE TRIGGER IF NOT EXISTS {tableName}Counts_UpdateTrigger
										AFTER UPDATE OF dlState ON {tableName}
										BEGIN
											UPDATE MangaItemCounts
												SET quantity = quantity + 1
												WHERE sourceSite=NEW.sourceSite AND dlState=NEW.dlState;
											UPDATE MangaItemCounts
												SET quantity = quantity - 1
												WHERE sourceSite=OLD.sourceSite AND dlState=OLD.dlState;
										END;'''.format(tableName=table))


	print("Pre-Counting table items in table %s." % table)

	ret = conn.execute("SELECT DISTINCT(dlState) FROM {tableName};".format(tableName=table))
	rets = ret.fetchall()
	values = [val[0] for val in rets]
	values = set(values)




	values.add(-1)
	values.add(0)
	values.add(1)
	values.add(2)

	ret = conn.execute("SELECT DISTINCT(sourceSite) FROM {tableName};".format(tableName=table))
	rets = ret.fetchall()
	sources = [val[0] for val in rets]


	print("Hooks created. Doing initial table item count")


	for source in sources:
		for val in values:
			ret = conn.execute("""SELECT COUNT(*) FROM {tableName} WHERE sourceSite=? AND dlState=?;""".format(tableName=table), (source, val))
			count = ret.fetchall().pop()[0]
			conn.execute("INSERT INTO MangaItemCounts (sourceSite, dlState, quantity) VALUES (?, ?, ?);", (source, val, count))

	print("Items counted. Good to go!")

	conn.commit()

