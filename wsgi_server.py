
#pylint: disable-msg=F0401, W0142


import runStatus
runStatus.preloadDicts = False


from pyramid.config import Configurator
from pyramid.response import Response, FileIter, FileResponse
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
import urllib.parse
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
import psycopg2
import traceback
import statusManager as sm

import mimetypes

reasons = '''

<!--
So.... Yeah. Many browsers don't display custom 404 pages if the content
is < 512 bytes long. Because reasons.

Anyways, pad that shit out so it actually works.
______________ ___ .___  _________ __________  _____    ___________________
\__    ___/   |   \|   |/   _____/ \______   \/  _  \  /  _____/\_   _____/
  |    | /    ~    \   |\_____  \   |     ___/  /_\  \/   \  ___ |    __)_
  |    | \    Y    /   |/        \  |    |  /    |    \    \_\  \|        \
  |____|  \___|_  /|___/_______  /  |____|  \____|__  /\______  /_______  /
                \/             \/                   \/        \/        \/
  ___ ___    _____    _________ ___________________    _____________________
 /   |   \  /  _  \  /   _____/ \__    ___/\_____  \   \______   \_   _____/
/    ~    \/  /_\  \ \_____  \    |    |    /   |   \   |    |  _/|    __)_
\    Y    /    |    \/        \   |    |   /    |    \  |    |   \|        \
 \___|_  /\____|__  /_______  /   |____|   \_______  /  |______  /_______  /
       \/         \/        \/                     \/          \/        \/
   _____   ________ _____________________ ______________ ______________ _______
  /     \  \_____  \\______   \_   _____/ \__    ___/   |   \_   _____/ \      \
 /  \ /  \  /   |   \|       _/|    __)_    |    | /    ~    \    __)_  /   |   \
/    Y    \/    |    \    |   \|        \   |    | \    Y    /        \/    |    \
\____|__  /\_______  /____|_  /_______  /   |____|  \___|_  /_______  /\____|__  /
        \/         \/       \/        \/                  \/        \/         \/
 .____________________   _______________.___.______________________ _________
 |   ____/_   \_____  \  \______   \__  |   |\__    ___/\_   _____//   _____/
 |____  \ |   |/  ____/   |    |  _//   |   |  |    |    |    __)_ \_____  \
 /       \|   /       \   |    |   \\____   |  |    |    |        \/        \
/______  /|___\_______ \  |______  // ______|  |____|   /_______  /_______  /
       \/             \/         \/ \/                          \/        \/
___________________ __________    ________________________ _____________.___________
\_   _____/\_____  \\______   \  /   _____/\__    ___/    |   \______   \   \______ \
 |    __)   /   |   \|       _/  \_____  \   |    |  |    |   /|     ___/   ||    |  \
 |     \   /    |    \    |   \  /        \  |    |  |    |  / |    |   |   ||    `   \
 \___  /   \_______  /____|_  / /_______  /  |____|  |______/  |____|   |___/_______  /
     \/            \/       \/          \/                                          \/
____________________ ___________________________  _________  ________  .____
\______   \______   \\_____  \__    ___/\_____  \ \_   ___ \ \_____  \ |    |
 |     ___/|       _/ /   |   \|    |    /   |   \/    \  \/  /   |   \|    |
 |    |    |    |   \/    |    \    |   /    |    \     \____/    |    \    |___
 |____|    |____|_  /\_______  /____|   \_______  /\______  /\_______  /_______ \
                  \/         \/                 \/        \/         \/        \/
_____________________   _____    _________________    _______    _________
\______   \_   _____/  /  _  \  /   _____/\_____  \   \      \  /   _____/
 |       _/|    __)_  /  /_\  \ \_____  \  /   |   \  /   |   \ \_____  \
 |    |   \|        \/    |    \/        \/    |    \/    |    \/        \
 |____|_  /_______  /\____|__  /_______  /\_______  /\____|__  /_______  /
        \/        \/         \/        \/         \/         \/        \/

-->
'''

def fix_matchdict(request):
	if request.matchdict:
		for key, values in request.matchdict.items():
			if type(values) is str:
				request.matchdict[key] = values.encode("latin-1").decode("utf-8")
			else:
				request.matchdict[key] = tuple(value.encode("latin-1").decode("utf-8") for value in values)


def errorPage(errorStr, moreInfo=False):

	if moreInfo:
		moreInfo = '''
		<div>
			{moreInfo}
		</div>
		'''.format(moreInfo=moreInfo)
	else:
		moreInfo = ''

	responseBody = '''
	<html>
		<head>
			<title>Error!</title>
		</head>
		<body>
			<div>
				<h3>{errorStr}</h3>
			</div>
			{moreInfo}
		</body>
	</html>

	'''.format(errorStr=errorStr, moreInfo=moreInfo)

	responseBody += reasons
	return Response(status_int=404, body=responseBody)


class PageResource(object):

	log = logging.getLogger("Main.WebSrv")

	conn = None  # Shaddup, pylint.

	def __init__(self):
		self.old_directory    = settings.webCtntPath
		self.mvc_directory    = settings.webMvcPath
		self.static_directory = settings.staticCtntPath

		# self.dirProxy = nameTools.DirNameProxy(settings.mangaFolders)
		self.dbPath = settings.DATABASE_DB_NAME
		self.lookupEngine_base = TemplateLookup(directories=[self.old_directory], module_directory='./ctntCache', strict_undefined=True)
		self.lookupEngine_mvc  = TemplateLookup(directories=[self.mvc_directory], module_directory='./ctntCache', strict_undefined=True)

		self.openDB()

		self.sessionManager = sessionManager.SessionPoolManager()
		self.apiInterface = apiHandler.ApiInterface(self.conn)

		mimetypes.init()

		cherrypy.engine.subscribe("exit", self.closeDB)


	def openDB(self):
		self.log.info("WSGI Server Opening DB...")
		self.log.info("DB Path = %s", self.dbPath)

		# Local sockets are MUCH faster if the DB is on the same machine as the server
		# Try a local connection. fall back to IP socket only if local connection fails.
		try:
			self.conn = psycopg2.connect(dbname=settings.DATABASE_DB_NAME, user=settings.DATABASE_USER,password=settings.DATABASE_PASS)
		except psycopg2.OperationalError:
			self.conn = psycopg2.connect(host=settings.DATABASE_IP, dbname=settings.DATABASE_DB_NAME, user=settings.DATABASE_USER,password=settings.DATABASE_PASS)

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


	def getRawContent(self, reqPath, context):
		print("Raw content request!", reqPath, context)

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
			return self.getPageHaveAuth(request, context=self.old_directory, engine=self.lookupEngine_base)


	def getMvcPage(self, request):

		# All the "Pages" in the new interface system are routed by code in the mako files,
		# rather then by pyramid. This is (mostly) done because modifying the pyramid
		# routing requires restarting the entire server, which itself requires
		# re-instantiating all the watched directories. This is rather prohibitive in
		# terms of load-time.
		request.environ['PATH_INFO'] = request.environ['PATH_INFO'][2:]

		redir = self.checkAuth(request)
		if redir:
			return redir


		absolute_path = os.path.join(self.mvc_directory, 'base_route.mako')
		reqPath = os.path.normpath(absolute_path)
		relPath = reqPath.replace(self.mvc_directory, "")
		pgTemplate = self.lookupEngine_mvc.get_template(relPath)


		self.log.info("Request for MVC-based mako page %s", reqPath)
		pageContent = pgTemplate.render_unicode(request=request, sqlCon=self.conn)
		self.log.info("Mako page Rendered %s", reqPath)

		return Response(body=pageContent)


	def getMvcResource(self, request):

		# This janky hack chops out the path-prefix for the new web UI version.
		# This is done by modifying the request, but because the `request.path`
		# parameter is a getter that internally looks at the request.environ dict,
		# we have to fix it there, rather then just assigning to `request.path`.
		request.environ['PATH_INFO'] = request.environ['PATH_INFO'][2:]

		redir = self.checkAuth(request)
		if redir:
			return redir
		else:
			return self.getPageHaveAuth(request, context=self.mvc_directory, engine=self.lookupEngine_mvc)

	def findTemplateFile(self, reqPath, context):

		# Check if there is a mako file at the path, and choose that preferentially over other files.
		# Includes adding `.mako` to the path if needed.

		templatePostFixes = ['.mako', '.mako.css']

		for searchPostfix in templatePostFixes:

			if reqPath.endswith(searchPostfix):
				makoPath = reqPath
			else:
				makoPath = reqPath + searchPostfix


			mako_absolute_path = os.path.join(context, makoPath)
			makoPath = os.path.normpath(mako_absolute_path)

			if os.path.exists(makoPath):
				if not makoPath.startswith(context):
					raise IOError()

				return makoPath, True


		absolute_path = os.path.join(self.static_directory, reqPath)
		reqPath = os.path.normpath(absolute_path)

		# Block attempts to access directories outside of the content dir
		if not reqPath.startswith(self.static_directory):
			print("reqPath:", reqPath)
			raise IOError()

		return reqPath, False

	# @profile(immediate=True, entries=150)
	def getPageHaveAuth(self, request, context, engine):

		if not "cookieid" in request.session or not request.session["cookieid"] in self.sessionManager:

			request.session["cookieid"] = self.sessionManager.getNewSessionKey()
			request.session.changed()


		fix_matchdict(request)

		self.log.info("Starting Serving old-style request from %s", request.remote_addr)
		reqPath = request.path.lstrip("/")
		if not reqPath.split("/")[-1]:
			reqPath += "index.mako"
			self.log.info("Appending 'index.mako'")


		reqPath, isTemplate = self.findTemplateFile(reqPath, context)

		print("Content path = ", reqPath, os.path.exists(reqPath))
		try:

			# Conditionally parse and render mako files.
			if isTemplate:
				relPath = reqPath.replace(context, "")
				pgTemplate = engine.get_template(relPath)

				self.log.info("Request for mako page %s", reqPath)
				pageContent = pgTemplate.render_unicode(request=request, sqlCon=self.conn)
				self.log.info("Mako page Rendered %s", reqPath)

				if reqPath.endswith(".css"):
					return Response(body=pageContent, content_type='text/css')
				else:
					return Response(body=pageContent)

			else:
				return self.getRawContent(reqPath, self.static_directory)

		except mako.exceptions.TopLevelLookupException:
			self.log.error("404 Request for page at url: %s", reqPath)
			pgTemplate = engine.get_template("error.mako")
			pageContent = pgTemplate.render_unicode(request=request, sqlCon=self.conn, tracebackStr=traceback.format_exc(), error_str="NO PAGE! 404")
			return Response(body=pageContent)
		except:
			self.log.error("Page rendering error! url: %s", reqPath)
			self.log.error(traceback.format_exc())
			pgTemplate = engine.get_template("error.mako")
			pageContent = pgTemplate.render_unicode(request=request, sqlCon=self.conn, tracebackStr=traceback.format_exc(), error_str="EXCEPTION! WAT?")
			return Response(body=pageContent)


	def checkAuth(self, request):
		return None

		userid = pys.authenticated_userid(request)
		if userid is None:
			return HTTPFound(location=request.route_url('login'))





	def sign_in_out(self, request):
		fix_matchdict(request)
		username = request.POST.get('username')
		password = request.POST.get('password')
		if username:
			self.log.info("Login attempt: u = %s, pass = %s", username, password)
			if username in users and users[username] == password:
				self.log.info("Successful Login!")
				age = 60*60*24*32
				headers = pys.remember(request, username, max_age='%d' % age)

				reqPath = request.path.lstrip("/")

				reqPath = reqPath + ".mako"
				pgTemplate = self.lookupEngine_base.get_template(reqPath)
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

	def getBookCover(self, request):
		try:
			seqId = int(request.matchdict["coverid"])
		except ValueError:
			return errorPage("That's not a integer ID!", moreInfo='Are you trying something bad?')


		cur = self.conn.cursor()
		cur.execute("BEGIN")
		cur.execute("""SELECT
					filename, relPath
				FROM
					series_covers
				WHERE
					id=%s;""", (seqId, ))
		item = cur.fetchone()
		if not item:
			self.log.warn("Request for cover with ID '%s' failed because it's not in the database.", seqId)
			return errorPage("Cover not found in cover item database!")

		fileName, fPath = item
		coverPath = os.path.join(settings.coverDirectory, fPath)
		if not os.path.exists(coverPath):
			self.log.error("Request for cover with ID '%s' failed because the file is missing!", seqId)
			return errorPage("Cover found, but the file is missing!")

		print(coverPath, os.path.exists(coverPath))
		ftype, dummy_coding = mimetypes.guess_type(fileName)

		if ftype:
			return FileResponse(path=coverPath, content_type=ftype)
		return FileResponse(path=coverPath)

	# New reader!

	def readerTwoPages(self, request):
		fix_matchdict(request)
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

		pgTemplate = self.lookupEngine_base.get_template('reader2/render.mako')

		self.log.info("Request for mako page %s", 'reader2/render.mako')
		pageContent = pgTemplate.render_unicode(request=request, sqlCon=self.conn, sessionArchTool=session)
		self.log.info("Mako page Rendered %s", 'reader2/render.mako')
		return Response(body=pageContent)



	def readerTwoPorn(self, request):
		fix_matchdict(request)
		self.log.info("Request for path: %s", request.path)
		if not "cookieid" in request.session or not request.session["cookieid"] in self.sessionManager:
			self.log.warning("Deeplink to Pron content without session cooke! Redirecting.")
			return HTTPFound(location=request.route_url('root'))

		session = self.sessionManager[request.session["cookieid"]]
		redir = self.checkAuth(request)
		if redir:
			return redir

		pgTemplate = self.lookupEngine_base.get_template('reader2/renderPron.mako')

		self.log.info("Request for mako page %s", 'reader2/renderPron.mako')
		pageContent = pgTemplate.render_unicode(request=request, sqlCon=self.conn, sessionArchTool=session)
		self.log.info("Mako page Rendered %s", 'reader2/renderPron.mako')
		return Response(body=pageContent)


	def readerTwoContent(self, request):
		fix_matchdict(request)

		self.log.info("Request for path: %s", request.path)
		if not "cookieid" in request.session or not request.session["cookieid"] in self.sessionManager:
			self.log.warning("Deeplink to Manga content without session cooke! Redirecting.")
			return HTTPFound(location=request.route_url('root'))

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



	def renderBook(self, request):
		return self.renderBookFromTable('book_items', request)

	def renderBookWestern(self, request):
		return self.renderBookFromTable('book_western_items', request)

	def renderBookFromTable(self, table, request):
		fix_matchdict(request)
		self.log.info("Request for book content. Matchdict = '%s'", request.params)

		if "url" in request.params or 'mdsum' in request.params:

			if 'url' in request.params:
				itemUrl = urllib.parse.unquote(request.params["url"])
				print("ItemURL: ", itemUrl)
				# self.conn
				cur = self.conn.cursor()
				cur.execute('BEGIN')
				cur.execute("SELECT mimetype, fsPath, url, distance, dbid FROM {tableName} WHERE url=%s;".format(tableName=table), (itemUrl, ))

				ret = cur.fetchall()

				if not ret:
					self.log.warn("Request for book content '%s' failed because it's not in the database.", itemUrl)
					responseBody = '''
					<html>
						<head>
							<title>Item not found!</title>
						</head>
						<body>
							<div>
								<h3>Item not found in Book item database!</h3>
							</div>
							<div>
								<a href='{url}'>Try to retreive from original source</a>
							</div>
						</body>
					</html>

					'''.format(url=itemUrl)
					responseBody += reasons
					return Response(status_int=404, body=responseBody)

			elif 'mdsum' in request.params:
				itemHash = urllib.parse.unquote(request.params["mdsum"])
				print("ItemHash: ", itemHash)
				# self.conn
				cur = self.conn.cursor()
				cur.execute('BEGIN')
				cur.execute("SELECT mimetype, fsPath, url FROM {tableName} WHERE fhash=%s;".format(tableName=table), (itemHash, ))

				ret = cur.fetchall()
				print(ret)
				if not ret:
					self.log.warn("Request for book content '%s' failed because it's not in the database.", itemHash)
					responseBody = '''
					<html>
						<head>
							<title>Item not found!</title>
						</head>
						<body>
							<div>
								<h3>Item with hash {itemhash} not found in Book item database!</h3>
							</div>
						</body>
					</html>



					'''.format(itemhash=itemHash)
					responseBody += reasons
					return Response(status_int=404, body=responseBody)

			requestData = ret.pop()
			mimetype, fsPath, itemUrl, distance, dbid = requestData

			if not mimetype:
				self.log.warn("Request for book content '%s' failed because the file has not been retreived yet.", request.params)


				pgTemplate = self.lookupEngine_base.get_template('books/access_error.mako')
				pageContent = pgTemplate.render_unicode(request=request, sqlCon=self.conn, extradat=requestData)
				pageContent += reasons
				return Response(status_int=404, body=pageContent)

			elif not 'text' in mimetype:
				if not os.path.exists(fsPath):
					self.log.warn("Request for book resource content '%s', which is missing.", request.params)


					return Response(status_int=404, body='File is missing! Has it not been fetched yet?')
				self.log.info("Request for book resource content '%s'", request.params)
				return FileResponse(path=fsPath, content_type=mimetype)



		pgTemplate = self.lookupEngine_base.get_template('books/render.mako')
		self.log.info("Rendering mako page %s", 'books/render.mako')
		pageContent = pgTemplate.render_unicode(request=request, sqlCon=self.conn)
		self.log.info("Mako page Rendered %s", 'books/render.mako')
		return Response(body=pageContent)



def buildApp():

	resource = PageResource()

	authn_policy = AuthTktAuthenticationPolicy('lolwattttt', hashalg='sha256', callback=userCheck)
	authz_policy = ACLAuthorizationPolicy()

	sessionFactory = UnencryptedCookieSessionFactoryConfig('watwatinthebat')

	config = Configurator(session_factory = sessionFactory)

	# config.add_settings({"debugtoolbar.hosts" : ["0.0.0.0/0", "10.1.1.4"]})
	# config.include('pyramid_debugtoolbar')


	config.set_authentication_policy(authn_policy)
	config.set_authorization_policy(authz_policy)

	# config.add_route(name='login',                   pattern='/login')
	# config.add_route(name='do_login',                pattern='/login-check')
	# config.add_route(name='auth',                    pattern='/login')


	config.add_route(name='book-cover',             pattern='/books/cover/{coverid}')

	config.add_route(name='book-render',             pattern='/books/render')
	config.add_route(name='book-render-western',     pattern='/books/render-w')


	config.add_route(name='reader-redux-container', pattern='/reader2/browse/*page')
	config.add_route(name='reader-redux-content',   pattern='/reader2/file/{sequenceid}')

	config.add_route(name='porn-get-arch',          pattern='/pron/read/{mId}')
	config.add_route(name='porn-get-images',        pattern='/pron/image/{sequenceid}')

	config.add_route(name='api',                    pattern='/api')
	config.add_route(name='static-file',            pattern='/js')
	config.add_route(name='root',                   pattern='/')


	config.add_route(name='mvc_rsc',               pattern='/r/*page')
	config.add_route(name='mvc_style',             pattern='/m/*page')

	config.add_route(name='leaf',                  pattern='/*page')

	config.add_view(resource.getBookCover,                            route_name='book-cover')

	config.add_view(resource.readerTwoPages,         http_cache=0, route_name='reader-redux-container')
	config.add_view(resource.readerTwoPorn,          http_cache=0, route_name='porn-get-arch')

	config.add_view(resource.readerTwoContent,       http_cache=0, route_name='reader-redux-content')
	config.add_view(resource.readerTwoContent,       http_cache=0, route_name='porn-get-images')

	config.add_view(resource.getPage,                              route_name='static-file')
	config.add_view(resource.renderBook,             http_cache=0, route_name='book-render')
	config.add_view(resource.renderBookWestern,      http_cache=0, route_name='book-render-western')
	config.add_view(resource.getPage,                http_cache=0, route_name='root')
	config.add_view(resource.getPage,                http_cache=0, route_name='leaf')
	config.add_view(resource.getPage,                http_cache=0, context=NotFound)

	config.add_view(resource.getApi,                 http_cache=0, route_name='api')


	config.add_view(resource.getMvcPage,             http_cache=0, route_name='mvc_style')
	config.add_view(resource.getMvcResource,         http_cache=0, route_name='mvc_rsc')




	# config.add_view(route_name='auth', match_param='action=in', renderer='string', request_method='POST')
	# config.add_view(route_name='auth', match_param='action=out', renderer='string')

	app = config.make_wsgi_app()


	return app


app = buildApp()
