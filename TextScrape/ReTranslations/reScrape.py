
import logSetup
if __name__ == "__main__":
	print("Initializing logging")
	logSetup.initLogging()

import TextScrape.TextScrapeBase

import bs4
import urllib.parse
import os.path
import hashlib
import webFunctions

import TextScrape.ReTranslations.gDocParse as gdp

class ReScrape(TextScrape.TextScrapeBase.TextScraper):
	tableKey = 'retrans'
	loggerPath = 'Main.Re:Trans'
	pluginName = 'ReTransScrape'

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	threads = 1


	startUrl = "https://docs.google.com/document/d/1ljoXDy-ti5N7ZYPbzDsj5kvYFl3lEWaJ1l3Lzv1cuuM/preview"
	baseUrl = "https://docs.google.com/document/"

	badwords = []


	def cleanPage(self, contents):
		soup = bs4.BeautifulSoup(contents)
		title = soup.title.get_text().strip()

		for span in soup.find_all("span"):
			span['style'] = ''

		return title, soup.prettify()


	def extractLinks(self, pageCtnt):
		soup = bs4.BeautifulSoup(pageCtnt)

		for link in soup.find_all("a"):

			# Skip empty anchor tags
			try:
				turl = link["href"]
			except KeyError:
				continue



			url = urllib.parse.urljoin(self.baseUrl, turl)
			url = gdp.GDocExtractor.isGdocUrl(url)
			# domain filtering is done in isGdocUrl
			if not url:
				continue

			self.log.info("Resolved URL = '%s'", url)


			# Remove any URL fragments causing multiple retreival of the same resource.
			url = url.split("#")[0]

			# upsert for `url`. Reset dlstate if needed

			self.newLinkQueue.put(url)


	def convertToReaderImage(self, url):
		if url in self.fMap:
			url = self.fMap[url]
		else:
			raise ValueError("Unknown image URL! = '%s'" % url)

		url = '/books/render?url=%s' % urllib.parse.quote(url)
		return url



	def processPage(self, url, content):

		dummy_fName, content = content

		pgTitle, pgBody = self.cleanPage(content)

		self.extractLinks(content)
		self.log.info("Page title = '%s'", pgTitle)
		pgBody = self.relink(pgBody)

		self.updateDbEntry(url=url, title=pgTitle, contents=pgBody, mimetype='text/html', dlstate=2)



	# Retreive remote content at `url`, call the appropriate handler for the
	# transferred content (e.g. is it an image/html page/binary file)
	def retreiveItemFromUrl(self, url):
		self.log.info("Fetching page '%s'", url)
		extr = gdp.GDocExtractor(url)

		mainPage, resources = extr.extract()





		self.fMap = {}


		for fName, mimeType, content in resources:



			m = hashlib.md5()
			m.update(content)
			fHash = m.hexdigest()

			hashName = "Re:Trans-"+fHash

			self.fMap[fName] = hashName

			fName = os.path.split(fName)[-1]

			self.log.info("Resource = '%s', '%s', '%s'", fName, mimeType, hashName)
			if mimeType in ["image/gif", "image/jpeg", "image/pjpeg", "image/png", "image/svg+xml", "image/vnd.djvu"]:
				self.log.info("Processing resource '%s' as an image file. (mimetype: %s)", fName, mimeType)
				self.upsert(hashName, istext=False)
				self.saveFile(hashName, mimeType, fName, content)
			elif mimeType in ["application/octet-stream"]:
				self.log.info("Processing '%s' as an binary file.", url)
				self.upsert(hashName, istext=False)
				self.saveFile(hashName, mimeType, fName, content)
			else:
				self.log.warn("Unknown MIME Type? '%s', Url: '%s'", mimeType, url)

		if len(resources) == 0:
			self.log.info("File had no resource content!")


		self.processPage(url, mainPage)




def test():
	scrp = ReScrape()
	scrp.crawl()


if __name__ == "__main__":
	test()

