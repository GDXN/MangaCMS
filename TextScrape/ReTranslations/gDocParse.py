

import bs4

import re
import io


import zipfile
import webFunctions
import mimetypes

def isGdocUrl(url):
	gdocBaseRe = re.compile(r'(https?://docs.google.com/document/d/[-_0-9a-zA-Z]+?)/preview')
	return gdocBaseRe.search(url)


class GDocExtractor(object):


	wg = webFunctions.WebGetRobust(logPath="Main.GDoc.Web")

	def __init__(self, targetUrl):

		url = isGdocUrl(targetUrl)
		if not url:
			raise ValueError("Passed URL '%s' is not a google document?" % targetUrl)

		self.url = url.group(1)+'/export?format=zip'
		self.refererUrl = targetUrl

		self.document = ''

		self.currentChunk = ''



	def extract(self):
		arch, fName = self.wg.getFileAndName(self.url, addlHeaders={'Referer': self.refererUrl})

		baseName = fName.split(".")[0]

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
