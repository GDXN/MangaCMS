
def migrateToTable(conn, fromStr, toTableName):
	print("Creating %s table" % toTableName)
	conn.execute('''CREATE TABLE IF NOT EXISTS {tableName} (
										dbId          INTEGER PRIMARY KEY,
										sourceSite    TEXT NOT NULL,
										dlState       text NOT NULL,
										sourceUrl     text UNIQUE NOT NULL,
										retreivalTime real NOT NULL,
										lastUpdate    real DEFAULT 0,
										sourceId      text,
										seriesName    text,
										fileName      text,
										originName    text,
										downloadPath  text,
										flags         text,
										tags          text,
										note          text);'''.format(tableName=toTableName))


	ret = conn.execute('''SELECT
							sourceSite,
							dlState,
							sourceUrl,
							retreivalTime,
							lastUpdate,
							sourceId,
							seriesName,
							fileName,
							originName,
							downloadPath,
							flags,
							tags,
							note
						FROM AllMangaItems
						WHERE {whereStr};
						'''.format(whereStr=fromStr))
	print("Table created. Migrating data")
	for row in ret.fetchall():
		conn.execute('''INSERT INTO {tableName} (

							sourceSite,
							dlState,
							sourceUrl,
							retreivalTime,
							lastUpdate,
							sourceId,
							seriesName,
							fileName,
							originName,
							downloadPath,
							flags,
							tags,
							note
							)
						VALUES (?,
								?,
								?,
								?,
								?,
								?,
								?,
								?,
								?,
								?,
								?,
								?,
								?)'''.format(tableName=toTableName), row)
	print("Creating indexes")
	conn.execute('''CREATE INDEX IF NOT EXISTS %s ON %s (sourceSite)'''                 % ("%s_source_index"     % toTableName, toTableName))
	conn.execute('''CREATE INDEX IF NOT EXISTS %s ON %s (retreivalTime)'''              % ("%s_time_index"       % toTableName, toTableName))
	conn.execute('''CREATE INDEX IF NOT EXISTS %s ON %s (lastUpdate)'''                 % ("%s_lastUpdate_index" % toTableName, toTableName))
	conn.execute('''CREATE INDEX IF NOT EXISTS %s ON %s (sourceUrl)'''                  % ("%s_url_index"        % toTableName, toTableName))
	conn.execute('''CREATE INDEX IF NOT EXISTS %s ON %s (seriesName collate nocase)'''  % ("%s_seriesName_index" % toTableName, toTableName))
	conn.execute('''CREATE INDEX IF NOT EXISTS %s ON %s (tags       collate nocase)'''  % ("%s_tags_index"       % toTableName, toTableName))
	conn.execute('''CREATE INDEX IF NOT EXISTS %s ON %s (flags      collate nocase)'''  % ("%s_flags_index"      % toTableName, toTableName))
	conn.execute('''CREATE INDEX IF NOT EXISTS %s ON %s (dlState)'''                    % ("%s_dlState_index"    % toTableName, toTableName))
	conn.execute('''CREATE INDEX IF NOT EXISTS %s ON %s (originName)'''                 % ("%s_originName_index" % toTableName, toTableName))

	conn.commit()
	print("Done")


def doTableCounts(conn):
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



def schemaSix2Seven(conn):
	import logSetup
	logSetup.initLogging()

	print("Inserting base names into lookup name database")

	migrateToTable(conn, '(sourceSite="bt" OR sourceSite="sk" OR sourceSite="cz" OR sourceSite="mb" OR sourceSite="jz" OR sourceSite="mk" OR sourceSite="mt")', "MangaItems")
	migrateToTable(conn, "(sourceSite='pu' OR sourceSite='fu' OR sourceSite='djm' OR sourceSite='em')", "HentaiItems")
	print("Migrated!")

