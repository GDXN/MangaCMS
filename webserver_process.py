
import logging
import wsgi_server

import cherrypy
import threading
import nameTools as nt


import DbManagement.countCleaner
import DbManagement.logTrimmer

def trimDatabase():
	cc = DbManagement.countCleaner.CountCleaner()
	cc.clean()

	# Trim the log files.
	lc = DbManagement.logTrimmer.LogTrimmer()
	lc.clean()

def fixup_cherrypy_logs():
	loggers = logging.Logger.manager.loggerDict.keys()
	for name in loggers:
		if name.startswith('cherrypy.'):
			print("Fixing %s." % name)
			logging.getLogger(name).propagate = 0


def runServer():

	cherrypy.tree.graft(wsgi_server.app, "/")

	# Unsubscribe the default server
	cherrypy.server.unsubscribe()

	# Instantiate a new server object
	server = cherrypy._cpserver.Server()

	# Configure the server object
	server.socket_host = "0.0.0.0"
	server.socket_port = 8081
	server.thread_pool = 30

	# For SSL Support
	# server.ssl_module            = 'pyopenssl'
	# server.ssl_certificate       = 'ssl/certificate.crt'
	# server.ssl_private_key       = 'ssl/private.key'
	# server.ssl_certificate_chain = 'ssl/bundle.crt'

	# Subscribe this server
	server.subscribe()

	fixup_cherrypy_logs()


	# The filesystem watching mechanism breaks the autoreloader
	# It crashes on restart unless the whole python interpreter is restarted.
	# cherrypy.config.update({'engine.autoreload.on':False})

	houseKeepingTasks = []
	for name, classInstance in nt.__dict__.items():
		if  isinstance(classInstance, type) or not hasattr(classInstance, "NEEDS_REFRESHING"):
			continue
		print("Have item to schedule - ", name, classInstance, "every", classInstance.REFRESH_INTERVAL, "seconds.")
		task = cherrypy.process.plugins.BackgroundTask(classInstance.REFRESH_INTERVAL, classInstance.refresh)  # Check if dir-dicts need updating
		task.start()
		houseKeepingTasks.append(task)


	# Flatten tracking table for item counts. Hourly
	# I can't easily wire this into the dynamic lookup above, so it's still manual.
	housekeeper = cherrypy.process.plugins.BackgroundTask(60*60*1, trimDatabase)
	housekeeper.start()
	houseKeepingTasks.append(housekeeper)

	cherrypy.engine.monitorPlugin = MonitorPlugin(cherrypy.engine)
	cherrypy.engine.monitorPlugin.subscribe()

	if hasattr(cherrypy.engine, 'signal_handler'):
		cherrypy.engine.signal_handler.subscribe()


	# Start the server engine (Option 1 *and* 2)
	cherrypy.engine.start()
	cherrypy.engine.block()
	fixup_cherrypy_logs()



class MonitorPlugin(cherrypy.process.plugins.SimplePlugin):

	# Make it a borg class (all instances share state)
	_shared_state = {"running" : True}

	def __init__(self, *args, **kwargs):

		self.__dict__ = self._shared_state
		super(MonitorPlugin,self).__init__(*args, **kwargs)


	def stop(self):
		if self.running:
			print("Stopping directory observer")
			nt.dirNameProxy.stop()
			nt.dirsLookup.stop()
			nt.nameLookup.stop()
			print("Directory observer Stopped")


def serverProcess():

	webThread = threading.Thread(target=runServer)
	webThread.start()
	print("Starting observers in background.")
	nt.dirNameProxy.startDirObservers()
	while runStatus.run:
		time.sleep(0.1)

	print("Stopping server.")
	cherrypy.engine.exit()

	print("Server stopped")

