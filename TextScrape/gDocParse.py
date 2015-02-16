

import bs4

import re
import io
import logging

import zipfile
import webFunctions
import mimetypes
import urllib.parse
import urllib.error


class GDocExtractor(object):

	log = logging.getLogger("Main.GDoc")
	wg = webFunctions.WebGetRobust(logPath="Main.GDoc.Web")

	def __init__(self, targetUrl):

		isGdoc, url = self.isGdocUrl(targetUrl)
		if not isGdoc:
			raise ValueError("Passed URL '%s' is not a google document?" % targetUrl)

		self.url = url+'/export?format=zip'
		self.refererUrl = targetUrl

		self.document = ''

		self.currentChunk = ''

	@classmethod
	def getDriveFileUrls(cls, url):
		ctnt = cls.wg.getpage(url)

		# horrible keyhole optimization regex abomination
		# this really, /REALLY/ should be a actual parser.
		driveFolderRe = re.compile(r'(https://docs.google.com/document/d/[-_0-9a-zA-Z]+)')
		items = driveFolderRe.findall(ctnt)
		return set(items)

	@classmethod
	def isGdocUrl(cls, url):
		# This is messy, because it has to work through bit.ly redirects.
		# I'm just resolving them here, rather then keeping them around because it makes things easier.
		gdocBaseRe = re.compile(r'(https?://docs.google.com/document/d/[-_0-9a-zA-Z]+)')
		simpleCheck = gdocBaseRe.search(url)
		if simpleCheck and not url.endswith("/pub"):
			return True, simpleCheck.group(1)

		return False, url

	@classmethod
	def clearBitLy(cls, url):
		if "bit.ly" in url:

			try:

				dummy_ctnt, handle = cls.wg.getpage(url, returnMultiple=True)
				# Recurse into redirects
				return cls.clearBitLy(handle.geturl())

			except urllib.error.URLError:
				print("Error resolving redirect!")
				return None

		return url


	@classmethod
	def clearOutboundProxy(cls, url):
		'''
		So google proxies all their outbound links through a redirect so they can detect outbound links.
		This call strips them out if they are present.

		'''
		if url.startswith("http://www.google.com/url?q="):
			qs = urllib.parse.urlparse(url).query
			query = urllib.parse.parse_qs(qs)
			if not "q" in query:
				raise ValueError("No target?")

			return query["q"].pop()

		return url


	def extract(self):
		try:
			arch, fName = self.wg.getFileAndName(self.url, addlHeaders={'Referer': self.refererUrl})
		except IndexError:
			print("ERROR: Failure retreiving page!")
			return None, []

		baseName = fName.split(".")[0]

		if not isinstance(arch, bytes):
			if 'You need permission' in arch or 'Sign in to continue to Docs':
				self.log.critical("Retreiving zip archive failed?")
				self.log.critical("Retreived content type: '%s'", type(arch))
				raise TypeError("Cannot access document? Is it protected?")
			else:
				with open("tmp_page.html", "w") as fp:
					fp.write(arch)
				raise ValueError("Doc not valid?")

		zp = io.BytesIO(arch)
		zfp = zipfile.ZipFile(zp)

		resources = []
		baseFile = None

		for item in zfp.infolist():
			if not "/" in item.filename and not baseFile:
				contents = zfp.open(item).read()
				contents = bs4.UnicodeDammit(contents).unicode_markup

				baseFile = (item.filename, contents)

			elif baseName in item.filename and baseName:
				raise ValueError("Multiple base file items?")

			else:
				resources.append((item.filename, mimetypes.guess_type(item.filename)[0], zfp.open(item).read()))

		if not baseFile:
			raise ValueError("No base file found!")

		return baseFile, resources




def test():
	import webFunctions
	wg = webFunctions.WebGetRobust()

	# url = 'https://docs.google.com/document/d/1ljoXDy-ti5N7ZYPbzDsj5kvYFl3lEWaJ1l3Lzv1cuuM/preview'
	# url = 'https://docs.google.com/document/d/17__cAhkFCT2rjOrJN1fK2lBdpQDSO0XtZBEvCzN5jH8/preview'
	url = 'https://docs.google.com/document/d/1t4_7X1QuhiH9m3M8sHUlblKsHDAGpEOwymLPTyCfHH0/preview'



	parse = GDocExtractor(url)
	base, resc = parse.extract()
	# parse.getTitle()


	# with open("test.html", "wb") as fp:
	# 	fp.write(ret.encode("utf-8"))

if __name__ == "__main__":
	import logSetup
	if __name__ == "__main__":
		print("Initializing logging")
		logSetup.initLogging()

	test()
