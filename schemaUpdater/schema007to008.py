
def updateFsSafeNames(conn):

	import nameTools as nt

	ret = conn.execute("SELECT dbId, name FROM muNameList WHERE fsSafeName IS NULL;")
	for dbId, name in ret.fetchall():
		sName = nt.prepFilenameForMatching(name)
		conn.execute("UPDATE muNameList SET fsSafeName=? WHERE dbId=?;", (sName, dbId))


	conn.commit()


def update_8(conn):

	print("Fixing all cases where fsSafeName is null")
	updateFsSafeNames(conn)
	print("Done!")


