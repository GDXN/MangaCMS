
import schemaUpdater.schemaRevisioner

def test():

	schemaUpdater.schemaRevisioner.updateDatabaseSchema()

def updateFsSafeColumn():
	print("Rebuilding FS Safe column in NameMapping database")
	import schemaUpdater.schemaFour2Five
	import logSetup
	logSetup.initLogging()
	import settings
	import sqlite3
	conn = sqlite3.connect(settings.dbName, timeout=10)
	schemaUpdater.schemaFour2Five.updateFsSafeNameColumn(conn)
	print("Updated")
	import nameTools as nt
	nt.dirNameProxy.stop()
if __name__ == "__main__":
	# test()
	updateFsSafeColumn()

