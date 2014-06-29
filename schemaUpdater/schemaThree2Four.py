

def schemaThree2Four(conn):

	print("Removing MangaTraders colums from database.")


	conn.execute('''CREATE TABLE IF NOT EXISTS MangaSeries_Temp (
										dbId            INTEGER PRIMARY KEY,

										buName          text COLLATE NOCASE UNIQUE,
										buId            text COLLATE NOCASE UNIQUE,
										buTags          text,
										buGenre         text,
										buList          text,

										buArtist        text,
										buAuthor        text,
										buOriginState   text,
										buDescription   text,
										buRelState      text,

										readingProgress int,
										availProgress   int,

										rating          int,
										lastChanged     real,
										lastChecked     real,
										itemAdded       real NOT NULL
										);''')


	ret = conn.execute('''SELECT dbId,
							buName,
							buId,
							buTags,
							buGenre,
							buList,
							readingProgress,
							availProgress,
							rating,
							lastChanged,
							lastChecked,
							itemAdded
						FROM MangaSeries;
						''')
	for row in ret.fetchall():
		conn.execute('''INSERT INTO MangaSeries_Temp (dbId,
														buName,
														buId,
														buTags,
														buGenre,
														buList,
														readingProgress,
														availProgress,
														rating,
														lastChanged,
														lastChecked,
														itemAdded)
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
								?)''', row)

	conn.execute("DROP TABLE MangaSeries;")
	conn.execute("ALTER TABLE MangaSeries_Temp RENAME TO MangaSeries;")
	conn.commit()

