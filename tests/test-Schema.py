

import logSetup
if __name__ == "__main__":
	logSetup.initLogging()


import schemaUpdater.schemaRevisioner
import DbManagement.countCleaner

def test():

	# schemaUpdater.schemaRevisioner.updateDatabaseSchema()
	cc = DbManagement.countCleaner.CountCleaner()
	print(cc)
	cc.clean()

if __name__ == "__main__":
	test()
	# updateFsSafeColumn()

