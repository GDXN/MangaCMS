
import logSetup
if __name__ == "__main__":
	print("Initializing logging")
	logSetup.initLogging()

import TextScrape.TextScrapeBase

import markdown
import readability.readability
import bs4
import webFunctions


class Scrape(TextScrape.TextScrapeBase.TextScraper):
	tableKey = 'rtdtl'
	loggerPath = 'Main.RaiseTheDead.Scrape'
	pluginName = 'RaiseTheDeadScrape'

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	threads = 3

	baseUrl = "https://wartdf.wordpress.com/"
	startUrl = [
		baseUrl,
		'http://pastebin.com/C8cU0ZPq',
		'http://pastebin.com/Gm4xYe35',
		'http://pastebin.com/iGjtwjVR',
		'http://pastebin.com/VyPC3Kdn',
		'http://pastebin.com/NS6kwFvL',
		'http://pastebin.com/raw.php?i=C8cU0ZPq',
		'http://pastebin.com/raw.php?i=Gm4xYe35',
		'http://pastebin.com/raw.php?i=iGjtwjVR',
		'http://pastebin.com/raw.php?i=VyPC3Kdn',
		'http://pastebin.com/raw.php?i=NS6kwFvL',
		]


	# Any url containing any of the words in the `badwords` list will be ignored.
	badwords = [
				"/manga/",
				"/recruitment/",
				"wpmp_switcher=mobile",
				"account/begin_password_reset",
				"/comment-page-",

				# Why do people think they need a fucking comment system?
				'/?replytocom=',
				'#comments',

				# Mask out the PDFs
				"-online-pdf-viewer/",

				# Who the fuck shares shit like this anyways?
				"?share=",

				]

	decompose = [
		{'id'    :'header'},
		{'class' : 'widget-area'},
		{'id'    : 'primary'},
		{'id'    : 'footer'},
		{'class' : 'photo-meta'},
		{'class' : 'bit'},
		{'id'    : 'bit'},
		{'id'    : 'likes-other-gravatars'},
		{'id'    : 'sidebar'},
		{'id'    : 'carousel-reblog-box'},
		{'id'    : 'infinite-footer'},
		{'id'    : 'nav-above'},
		{'id'    : 'nav-below'},
		{'id'    : 'jp-post-flair'},
		{'id'    : 'comments'},
		{'class' : 'entry-utility'},

	]


	def cleanBtPage(self, inPage):

		# since readability strips tag attributes, we preparse with BS4,
		# parse with readability, and then do reformatting *again* with BS4
		# Yes, this is ridiculous.
		soup = bs4.BeautifulSoup(inPage)

		# Decompose all the parts we don't want
		for key in self.decompose:
			for instance in soup.find_all(True, attrs=key):
				instance.decompose()


		doc = readability.readability.Document(soup.prettify())
		doc.parse()
		content = doc.content()

		soup = bs4.BeautifulSoup(content)

		contents = ''


		# Relink all the links so they work in the reader.
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

		# Generate HTML string for /just/ the contents of the <body> tag.
		for item in soup.body.contents:
			if type(item) is bs4.Tag:
				contents += item.prettify()
			elif type(item) is bs4.NavigableString:
				contents += item
			else:
				print("Wat", item)

		title = doc.title()
		title = title.replace("Raising the Dead |", "")

		return title, contents



	def processPage(self, url, content, mimeType):


		pgTitle, pgBody = self.cleanBtPage(content)
		self.extractLinks(content, url=url)
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

		elif mimeType in ['text/plain']:
			self.log.info("Plain-text file. Processing with markdown.")

			# Take the first non-empty line, and just assume it's the title. It'll be close enough.
			title = content.strip().split("\n")[0].strip()

			content = markdown.markdown(content)

			self.updateDbEntry(url=url, title=title, contents=content, mimetype='text/html', dlstate=2)


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
	scrp = Scrape()
	scrp.crawl()
	# scrp.retreiveItemFromUrl(scrp.startUrl)


if __name__ == "__main__":
	test()




