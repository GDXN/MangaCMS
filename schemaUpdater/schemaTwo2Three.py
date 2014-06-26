

def schemaTwo2Three(conn):

	print("Ensuring commit hooks for table-size tracking exist.")


	conn.execute('''CREATE TABLE IF NOT EXISTS MangaItemCounts (
										sourceSite    text NOT NULL,
										dlState       real NOT NULL,
										quantity      int  DEFAULT 0,
										UNIQUE(sourceSite, dlState) ON CONFLICT REPLACE
										);''')

	# Increment on creation
	conn.execute('''CREATE TRIGGER IF NOT EXISTS MangaItemCounts_CreateTrigger
										AFTER INSERT ON AllMangaItems
										BEGIN
											UPDATE MangaItemCounts
												SET quantity = quantity + 1
												WHERE sourceSite=NEW.sourceSite AND dlState=NEW.dlState;
										END;''')

	# Deincrement on delete
	conn.execute('''CREATE TRIGGER IF NOT EXISTS MangaItemCounts_DeleteTrigger
										BEFORE DELETE ON AllMangaItems
										BEGIN
											UPDATE MangaItemCounts
												SET quantity = quantity - 1
												WHERE sourceSite=OLD.sourceSite AND dlState=OLD.dlState;
										END;''')

	# Deincrement on delete
	conn.execute('''CREATE TRIGGER IF NOT EXISTS MangaItemCounts_UpdateTrigger
										AFTER UPDATE OF dlState ON AllMangaItems
										BEGIN
											UPDATE MangaItemCounts
												SET quantity = quantity + 1
												WHERE sourceSite=NEW.sourceSite AND dlState=NEW.dlState;
											UPDATE MangaItemCounts
												SET quantity = quantity - 1
												WHERE sourceSite=OLD.sourceSite AND dlState=OLD.dlState;
										END;''')
	doTableCounts(conn)

def doTableCounts(conn):

	print("Pre-Counting table items.")

	ret = conn.execute("SELECT DISTINCT(dlState) FROM AllMangaItems;")
	rets = ret.fetchall()
	values = [val[0] for val in rets]
	values = set(values)


	values.add(-1)
	values.add(0)
	values.add(1)
	values.add(2)

	ret = conn.execute("SELECT DISTINCT(sourceSite) FROM AllMangaItems;")
	rets = ret.fetchall()
	sources = [val[0] for val in rets]


	print("Hooks created. Doing initial table item count")


	for source in sources:
		for val in values:
			ret = conn.execute("""SELECT COUNT(*) FROM AllMangaItems WHERE sourceSite=? AND dlState=?;""", (source, val))
			count = ret.fetchall().pop()[0]
			conn.execute("INSERT INTO MangaItemCounts (sourceSite, dlState, quantity) VALUES (?, ?, ?);", (source, val, count))

	print("Items counted. Good to go!")

	conn.commit()
