
import logSetup
if __name__ == "__main__":
	print("Initializing logging")
	logSetup.initLogging()

import TextScrape.SqlBase

import readability.readability
import bs4
import webFunctions

import TextScrape.ReTranslations.gDocParse as gdp

class ReScrape(TextScrape.SqlBase.TextScraper):
	tableKey = 'retrans'
	loggerPath = 'Main.Re:Trans'
	pluginName = 'ReTransScrape'

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	threads = 1


	startUrl = "https://docs.google.com/document/d/1t4_7X1QuhiH9m3M8sHUlblKsHDAGpEOwymLPTyCfHH0/preview"
	baseUrl = "https://docs.google.com/document/"

	badwords = []

	def cleanBtPage(self, inPage):
		parser = gdp.GDocParser(inPage)
		contents = parser.parse()

		title = parser.getTitle()

		return title, contents



	def processPage(self, url, content, mimeType):


		pgTitle, pgBody = self.cleanBtPage(content)
		self.extractLinks(pgBody)
		self.updateDbEntry(url=url, title=pgTitle, contents=pgBody, mimetype=mimeType, dlstate=2)


	# Retreive remote content at `url`, call the appropriate handler for the
	# transferred content (e.g. is it an image/html page/binary file)
	def retreiveItemFromUrl(self, url):
		self.log.info("Fetching page '%s'", url)
		content, fName, mimeType = self.getItem(url)

		links = []

		if mimeType == 'text/html':
			self.log.info("Processing '%s' as HTML.", url)
			self.processPage(url, content, mimeType)
		elif mimeType in ["image/gif", "image/jpeg", "image/pjpeg", "image/png", "image/svg+xml", "image/vnd.djvu"]:
			self.log.info("Processing '%s' as an image file.", url)
			self.saveFile(url, mimeType, fName, content)
		elif mimeType in ["application/octet-stream"]:
			self.log.info("Processing '%s' as an binary file.", url)
			self.saveFile(url, mimeType, fName, content)
		else:
			self.log.warn("Unknown MIME Type? '%s', Url: '%s'", mimeType, url)


		return links

def test():
	scrp = ReScrape()
	scrp.crawl()


if __name__ == "__main__":
	test()

