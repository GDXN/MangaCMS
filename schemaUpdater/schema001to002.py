

TABLES_TO_MERGE = {'MangaItems' : "mt", 'SkMangaItems' : "sk", 'CzMangaItems' : "cz", "DoujinMoeItems" : "djm", "FufufuuItems" : "fu"}
NEW_TABLE_NAME = "AllMangaItems"


def mergeInTable(conn, mergeInName, key):
	cur = conn.cursor()
	ret = cur.execute('''SELECT dlState,
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
								FROM %s;
								''' % mergeInName)
	ret = list(ret) # Extract all versions now.

	for dlState,       \
		sourceUrl,     \
		retreivalTime, \
		lastUpdate,    \
		sourceId,      \
		seriesName,    \
		fileName,      \
		originName,    \
		downloadPath,  \
		flags,         \
		tags,          \
		note in ret:

		cur.execute('''INSERT INTO %s (sourceSite,
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
									note)
								VALUES(
									?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
								);''' % NEW_TABLE_NAME,
								(
									key,
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
									note))


	print("Migrated table: ", mergeInName)

def updateOne2Two(conn):

	print("Migrating table from schema rev 1 to schema rev 2")


	conn.execute('''CREATE TABLE IF NOT EXISTS %s (
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
										note          text);''' % NEW_TABLE_NAME)

	conn.execute('''CREATE INDEX IF NOT EXISTS %s ON %s (sourceSite)'''                 % ("%s_source_index"        % NEW_TABLE_NAME, NEW_TABLE_NAME))
	conn.execute('''CREATE INDEX IF NOT EXISTS %s ON %s (retreivalTime)'''              % ("%s_time_index"          % NEW_TABLE_NAME, NEW_TABLE_NAME))
	conn.execute('''CREATE INDEX IF NOT EXISTS %s ON %s (sourceSite, retreivalTime)'''  % ("%s_src_time_index"      % NEW_TABLE_NAME, NEW_TABLE_NAME))
	conn.execute('''CREATE INDEX IF NOT EXISTS %s ON %s (lastUpdate)'''                 % ("%s_lastUpdate_index"    % NEW_TABLE_NAME, NEW_TABLE_NAME))
	conn.execute('''CREATE INDEX IF NOT EXISTS %s ON %s (sourceUrl)'''                  % ("%s_url_index"           % NEW_TABLE_NAME, NEW_TABLE_NAME))
	conn.execute('''CREATE INDEX IF NOT EXISTS %s ON %s (seriesName collate nocase)'''  % ("%s_seriesName_index"    % NEW_TABLE_NAME, NEW_TABLE_NAME))
	conn.execute('''CREATE INDEX IF NOT EXISTS %s ON %s (tags       collate nocase)'''  % ("%s_tags_index"          % NEW_TABLE_NAME, NEW_TABLE_NAME))
	conn.execute('''CREATE INDEX IF NOT EXISTS %s ON %s (flags      collate nocase)'''  % ("%s_flags_index"         % NEW_TABLE_NAME, NEW_TABLE_NAME))
	conn.execute('''CREATE INDEX IF NOT EXISTS %s ON %s (dlState)'''                    % ("%s_dlState_index"       % NEW_TABLE_NAME, NEW_TABLE_NAME))


	print("Created new aggregate database")

	for tableName in TABLES_TO_MERGE.keys():
		mergeInTable(conn, tableName, TABLES_TO_MERGE[tableName])
	print("Data merged. Dropping old tables")
	for tableName in TABLES_TO_MERGE.keys():
		conn.execute('''DROP TABLE %s;''' % tableName)
	conn.commit()
