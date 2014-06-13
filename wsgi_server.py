
#pylint: disable-msg=F0401, W0142

from pyramid.config import Configurator
from pyramid.response import Response, FileIter
from pyramid.exceptions import NotFound
from pyramid.httpexceptions import HTTPFound
from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.session import UnencryptedCookieSessionFactoryConfig

import pyramid.security as pys

import mako.exceptions
from mako.lookup import TemplateLookup
import cherrypy
import settings
import apiHandler

import sessionManager

import os.path
users = {"herp" : "wattttttt"}

# from profilehooks import profile

def userCheck(userid, dummy_request):
	if userid in users:
		return True
	else:
		return False

import logging
import sqlite3
import traceback
import statusManager as sm

import mimetypes


class PageResource(object):

	log = logging.getLogger("Main.WebSrv")

	def __init__(self):
		self.base_directory = settings.webCtntPath
		# self.dirProxy = nameTools.DirNameProxy(settings.mangaFolders)
		self.dbPath = settings.dbName
		self.lookupEngine = TemplateLookup(directories=[self.base_directory], module_directory='./ctntCache', strict_undefined=True)

		self.openDB()

		self.sessionManager = sessionManager.SessionPoolManager()
		self.apiInterface = apiHandler.ApiInterface(self.conn)

		mimetypes.init()

		cherrypy.engine.subscribe("exit", self.closeDB)


	def openDB(self):
		self.log.info("WSGI Server Opening DB...")
		self.log.info("DB Path = %s", self.dbPath)
		self.conn = sqlite3.connect(self.dbPath, check_same_thread=False)

		self.log.info("DB opened. Activating 'wal' mode")
		rets = self.conn.execute('''PRAGMA journal_mode=wal;''')
		rets = self.conn.execute('''PRAGMA locking_mode=EXCLUSIVE;''')
		rets = rets.fetchall()

		self.log.info("PRAGMA return value = %s", rets)

		sm.checkStatusTableExists()

	def closeDB(self):
		self.log.info("Closing DB...",)
		try:
			self.conn.close()
		except:
			self.log.error("wat")
			self.log.error(traceback.format_exc())
		self.log.info("done")



	def guessItemMimeType(self, itemName):
		mimeType = mimetypes.guess_type(itemName)
		self.log.info("Inferred MIME type %s for file %s", mimeType,  itemName)
		if mimeType:
			return mimeType[0]
		else:
			return "application/unknown"


	def getRawContent(self, reqPath):

		self.log.info("Request for raw content at URL %s", reqPath)
		with open(reqPath, "rb") as fp:
			ret = Response(body=fp.read())
			ret.content_type = self.guessItemMimeType(reqPath)

			return ret

	def getPage(self, request):
		redir = self.checkAuth(request)
		if redir:
			return redir
		else:
			return self.getPageHaveAuth(request)

	def checkProcessPath(self, reqPath):

		# Check if there is a mako file at the path, and choose that preferentially over other files.
		# Includes adding `.mako` to the path if needed.

		makoPath = reqPath + ".mako"

		absolute_path = os.path.join(self.base_directory, reqPath)
		reqPath = os.path.normpath(absolute_path)

		mako_absolute_path = os.path.join(self.base_directory, makoPath)
		makoPath = os.path.normpath(mako_absolute_path)

		if os.path.exists(makoPath):
			reqPath = makoPath

		# Block attempts to access directories outside of the content dir
		if not reqPath.startswith(self.base_directory):
			raise IOError()

		return reqPath

	# @profile(immediate=True, entries=150)
	def getPageHaveAuth(self, request):

		if not "cookieid" in request.session or not request.session["cookieid"] in self.sessionManager:

			request.session["cookieid"] = self.sessionManager.getNewSessionKey()
			request.session.changed()


		self.log.info("Starting Serving request")
		reqPath = request.path.lstrip("/")
		if not reqPath.split("/")[-1]:
			reqPath += "index.mako"

		reqPath = self.checkProcessPath(reqPath)

		# print("Content path = ", reqPath, os.path.exists(reqPath))
		try:

			# Conditionally parse and render mako files.
			if reqPath.endswith(".mako"):
				relPath = reqPath.replace(self.base_directory, "")
				pgTemplate = self.lookupEngine.get_template(relPath)

				self.log.info("Request for mako page %s", reqPath)
				pageContent = pgTemplate.render_unicode(request=request, sqlCon=self.conn)
				self.log.info("Mako page Rendered %s", reqPath)

				return Response(body=pageContent)
			else:
				return self.getRawContent(reqPath)

		except mako.exceptions.TopLevelLookupException:
			self.log.error("404 Request for page at url: %s", reqPath)
			pgTemplate = self.lookupEngine.get_template("error.mako")
			pageContent = pgTemplate.render_unicode(request=request, sqlCon=self.conn, tracebackStr=traceback.format_exc(), error_str="NO PAGE! 404")
			return Response(body=pageContent)
		except:
			self.log.error("Page rendering error! url: %s", reqPath)
			self.log.error(traceback.format_exc())
			pgTemplate = self.lookupEngine.get_template("error.mako")
			pageContent = pgTemplate.render_unicode(request=request, sqlCon=self.conn, tracebackStr=traceback.format_exc(), error_str="EXCEPTION! WAT?")
			return Response(body=pageContent)


	def checkAuth(self, request):
		return None

		userid = pys.authenticated_userid(request)
		if userid is None:
			return HTTPFound(location=request.route_url('login'))



	def readerBase(self, request):
		self.log.info("Request for path: %s", request.path)
		# print("Read file = ", request)
		# print("Session = ", request.session)
		if not "cookieid" in request.session or not request.session["cookieid"] in self.sessionManager:
			self.log.info("Creating session")
			request.session["cookieid"] = self.sessionManager.getNewSessionKey()
			request.session.changed()

		session = self.sessionManager[request.session["cookieid"]]

		redir = self.checkAuth(request)
		if redir:
			return redir

		pgTemplate = self.lookupEngine.get_template('reader/index.mako')

		self.log.info("Request for mako page %s", 'reader/index.mako')
		pageContent = pgTemplate.render_unicode(request=request, sqlCon=self.conn, sessionArchTool=session)
		self.log.info("Mako page Rendered %s", 'reader/index.mako')
		return Response(body=pageContent)


	def getMangaReaderForFile(self, request):
		self.log.info("Request for path: %s", request.path)
		if not "cookieid" in request.session or not request.session["cookieid"] in self.sessionManager:
			self.log.warning("Deeplink to Manga content without session cooke! Redirecting.")
			return HTTPFound(location=request.route_url('reader-startup'))

		session = self.sessionManager[request.session["cookieid"]]
		redir = self.checkAuth(request)
		if redir:
			return redir

		pgTemplate = self.lookupEngine.get_template('reader/read.mako')

		self.log.info("Request for mako page %s", 'reader/read.mako')
		pageContent = pgTemplate.render_unicode(request=request, sqlCon=self.conn, sessionArchTool=session)
		self.log.info("Mako page Rendered %s", 'reader/read.mako')
		return Response(body=pageContent)

	def getPornReaderForFile(self, request):
		self.log.info("Request for path: %s", request.path)
		if not "cookieid" in request.session or not request.session["cookieid"] in self.sessionManager:
			self.log.warning("Deeplink to Pron content without session cooke! Redirecting.")
			return HTTPFound(location=request.route_url('reader-startup'))

		session = self.sessionManager[request.session["cookieid"]]
		redir = self.checkAuth(request)
		if redir:
			return redir

		pgTemplate = self.lookupEngine.get_template('reader/pron.mako')

		self.log.info("Request for mako page %s", 'reader/pron.mako')
		pageContent = pgTemplate.render_unicode(request=request, sqlCon=self.conn, sessionArchTool=session)
		self.log.info("Mako page Rendered %s", 'reader/pron.mako')
		return Response(body=pageContent)

	def getImageKeyOffset(self, request):
		self.log.info("Request for path: %s", request.path)
		if not "cookieid" in request.session or not request.session["cookieid"] in self.sessionManager:
			return HTTPFound(location=request.route_url('reader-startup'))

		session = self.sessionManager[request.session["cookieid"]]
		redir = self.checkAuth(request)
		if redir:
			return redir

		seqId = int(request.matchdict["sequenceid"])
		itemFileHandle, itemPath = session.getItemByKey(seqId)
		response = request.response
		response.app_iter = FileIter(itemFileHandle)
		response.content_type = self.guessItemMimeType(itemPath)

		return response

	def sign_in_out(self, request):
		username = request.POST.get('username')
		password = request.POST.get('password')
		if username:
			self.log.info("Login attempt: u = %s, pass = %s" % (username, password))
			if username in users and users[username] == password:
				self.log.info("Successful Login!")
				age = 60*60*24*32
				headers = pys.remember(request, username, max_age='%d' % age)

				reqPath = request.path.lstrip("/")

				reqPath = reqPath + ".mako"
				pgTemplate = self.lookupEngine.get_template(reqPath)
				pageContent = pgTemplate.render_unicode(request=request)
				return Response(body=pageContent, headers=headers)

			else:
				self.log.info("Invalid user. Deleting cookie.")
				headers = pys.forget(request)
		else:
			self.log.info("No user specified - Deleting cookie.")
			headers = pys.forget(request)

		return HTTPFound(location=request.route_url('login'))


	def getApi(self, request):
		return self.apiInterface.handleApiCall(request)




def buildApp():

	resource = PageResource()

	authn_policy = AuthTktAuthenticationPolicy('lolwattttt', hashalg='sha256', callback=userCheck)
	authz_policy = ACLAuthorizationPolicy()

	sessionFactory = UnencryptedCookieSessionFactoryConfig('watwatinthebat')

	config = Configurator(session_factory = sessionFactory)


	config.set_authentication_policy(authn_policy)
	config.set_authorization_policy(authz_policy)

	# config.add_route(name='login',                   pattern='/login')
	# config.add_route(name='do_login',                pattern='/login-check')
	# config.add_route(name='auth',                    pattern='/login')
	# config.add_route(name='get-image-by-id',         pattern='/images/byid/{imageID}')
	# config.add_route(name='get-image-by-offset',     pattern='/images/byoffset/{artist}/{offset}')

	config.add_route(name='reader-startup',    pattern='/reader/')
	config.add_route(name='reader-dict',       pattern='/reader/{dict}')
	config.add_route(name='reader-get-files',  pattern='/reader/{dict}/{seriesName}')
	config.add_route(name='reader-get-arch',   pattern='/reader/{dict}/{seriesName}/{fileName}')
	config.add_route(name='reader-get-images', pattern='/reader/{dict}/{seriesName}/{fileName}/{sequenceid}')

	config.add_route(name='porn-get-arch',     pattern='/pron/{source}/{mId}')
	config.add_route(name='porn-get-images',   pattern='/pron/{source}/{mId}/{sequenceid}')

	config.add_route(name='api',               pattern='/api')
	config.add_route(name='static-file',       pattern='/js')
	config.add_route(name='root',              pattern='/')
	config.add_route(name='leaf',              pattern='/*page')

	# config.add_view(resource.getPageHaveAuth,          http_cache=0, route_name='login')
	# config.add_view(resource.sign_in_out,            http_cache=0, route_name='do_login')
	# config.add_view(resource.getImageById,           http_cache=0, route_name='get-image-by-id')
	# config.add_view(resource.getImageByArtistOffset, http_cache=0, route_name='get-image-by-offset')

	config.add_view(resource.readerBase,             http_cache=0, route_name='reader-startup')
	config.add_view(resource.readerBase,             http_cache=0, route_name='reader-dict')
	config.add_view(resource.readerBase,             http_cache=0, route_name='reader-get-files')
	config.add_view(resource.getMangaReaderForFile,  http_cache=0, route_name='reader-get-arch')
	config.add_view(resource.getPornReaderForFile,   http_cache=0, route_name='porn-get-arch')
	config.add_view(resource.getImageKeyOffset,      http_cache=0, route_name='reader-get-images')
	config.add_view(resource.getImageKeyOffset,      http_cache=0, route_name='porn-get-images')

	config.add_view(resource.getPage,                              route_name='static-file')
	config.add_view(resource.getPage,                http_cache=0, route_name='root')
	config.add_view(resource.getPage,                http_cache=0, route_name='leaf')
	config.add_view(resource.getPage,                http_cache=0, context=NotFound)

	config.add_view(resource.getApi,                 http_cache=0, route_name='api')


	# config.add_view(route_name='auth', match_param='action=in', renderer='string', request_method='POST')
	# config.add_view(route_name='auth', match_param='action=out', renderer='string')

	# config.include('pyramid_debugtoolbar')


	app = config.make_wsgi_app()


	return app


app = buildApp()
