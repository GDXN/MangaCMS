
import logSetup
if __name__ == "__main__":
	print("Initializing logging")
	logSetup.initLogging()

import TextScrape.TextScrapeBase

import readability.readability
import bs4
import webFunctions
import urllib.error

class GuheheScrape(TextScrape.TextScrapeBase.TextScraper):
	tableKey = 'guhehe'
	loggerPath = 'Main.Guhehe.Scrape'
	pluginName = 'GuheheScrape'

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	threads = 2


	baseUrl = "http://guhehe.net/"
	startUrl = 'http://guhehe.net/series/'

	badwords = [
				"/about/",
				"/join-us/",
				"/chat/",
				'&format=pdf',
				'?format=pdf',
				'?replytocom=',
				]

	positive_keywords = ['main_content']

	negative_keywords = ['mw-normal-catlinks',
						"printfooter",
						"mw-panel",
						'portal']


	decompose = [
				('header',  {'id':'main-header'}),
				('footer',  {'id':'main-footer'}),
				('section', {'id':'comment-wrap'}),
				('div',     {'id':'sidebar'}),
				]

	def cleanPage(self, inPage):

		soup = bs4.BeautifulSoup(inPage)
		for name, tagAttrs in self.decompose:

			for tag in soup.find_all(name, attrs=tagAttrs):
				tag.decompose()


		inPage = soup.prettify()
		doc = readability.readability.Document(inPage, positive_keywords=self.positive_keywords, negative_keywords=self.negative_keywords)
		doc.parse()
		content = doc.content()

		soup = bs4.BeautifulSoup(content)

		for aTag in soup.find_all("a"):
			try:
				aTag["href"] = self.convertToReaderUrl(aTag["href"])
			except KeyError:
				continue

		for imtag in soup.find_all("img"):
			try:
				imtag["src"] = self.convertToReaderUrl(imtag["src"])
			except KeyError:
				continue


		contents = ''

		for item in soup.body.contents:
			if type(item) is bs4.Tag:
				contents += item.prettify()
			elif type(item) is bs4.NavigableString:
				contents += item
			else:
				print("Wat", item)

		title = doc.title()
		title = title.replace('| guhehe.TRANSLATIONS', "")
		title = title.strip()

		return title, contents



	def processPage(self, url, content, mimeType):


		pgTitle, pgBody = self.cleanPage(content)
		self.extractLinks(content)
		self.updateDbEntry(url=url, title=pgTitle, contents=pgBody, mimetype=mimeType, dlstate=2)


	# Retreive remote content at `url`, call the appropriate handler for the
	# transferred content (e.g. is it an image/html page/binary file)
	def retreiveItemFromUrl(self, url):
		self.log.info("Fetching page '%s'", url)
		try:
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

		except urllib.error.URLError:
			self.log.warn("Page retreival failed!")
			self.updateDbEntry(url=url, dlstate=-1)






def test():
	scrp = GuheheScrape()
	scrp.crawl()
	# scrp.retreiveItemFromUrl(scrp.startUrl)
	# new = gdp.GDocExtractor.getDriveFileUrls('https://drive.google.com/folderview?id=0B-x_RxmzDHegRk5iblp4alZmSkU&usp=sharing')


if __name__ == "__main__":
	test()

