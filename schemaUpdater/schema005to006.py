
def migrateBaseNamesIntoLookup(conn):

	import nameTools as nt

	ret = conn.execute("SELECT buId, name FROM muNameList;")
	for buId, name in ret.fetchall():
		sName = nt.prepFilenameForMatching(name)
		conn.execute("INSERT INTO muNameList (buId, name, fsSafeName) VALUES (?, ?, ?);", (buId, name, sName))


	conn.commit()


def schemaFive2Six(conn):
	import logSetup
	logSetup.initLogging()

	print("Inserting base names into lookup name database")
	migrateBaseNamesIntoLookup(conn)
	print("Migrated!")


