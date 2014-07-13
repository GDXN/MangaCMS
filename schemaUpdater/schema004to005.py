
import sqlite3

def updateFsSafeNameColumn(conn):

	import nameTools as nt

	ret = conn.execute("SELECT dbId, name FROM muNameList;")
	for dbId, name in ret.fetchall():
		sName = nt.prepFilenameForMatching(name)
		conn.execute("UPDATE muNameList SET fsSafeName=? WHERE dbId=? AND name=?;", (sName, dbId, name))


	conn.commit()


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
	updateFsSafeNameColumn(conn)
	print("Column populated!")

	nt.dirNameProxy.stop()

