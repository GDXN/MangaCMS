
import sys
if sys.version_info < ( 3, 4):
	# python too old, kill the script
	sys.exit("This script requires Python 3.4 or newer!")


if __name__ == "__main__":
	import runStatus
	runStatus.preloadDicts = True


# mainScrape does actual schema updating. We just want to check the version, and bail
# out if it's too old.
import schemaUpdater.schemaRevisioner
schemaUpdater.schemaRevisioner.verifySchemaUpToDate()


import logSetup
logSetup.initLogging()

import webserver_process

if __name__ == "__main__":
	# It looks like cherrypy installs a ctrl+c handler, so I don't need to.
	webserver_process.serverProcess()
