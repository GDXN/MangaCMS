
import sqlite3

def schemaFour2Five(conn):
	import logSetup
	logSetup.initLogging()
	import nameTools as nt

	print("Adding column for filesystem-safe names to MangaUpdates table")

	try:
		conn.execute("ALTER TABLE muNameList ADD COLUMN fsSafeName text COLLATE NOCASE;")
		conn.execute('''CREATE INDEX IF NOT EXISTS %s ON %s (name collate nocase)''' % ("%s_fSafeName_name_index"     % "muNameList", "muNameList"))
		conn.commit()
	except sqlite3.OperationalError:
		print("Wat?")
		import traceback
		traceback.print_exc()

	print("Populating the new Filesystem-save colum from the plain name column")

	ret = conn.execute("SELECT dbId, name FROM muNameList;")
	for dbId, name in ret.fetchall():
		sName = nt.makeFilenameSafe(name)
		conn.execute("UPDATE muNameList SET fsSafeName=? WHERE dbId=?;", (sName, dbId))


	conn.commit()

	print("Column populated!")

	nt.dirNameProxy.stop()
