
import logSetup
if __name__ == "__main__":
	print("Initializing logging")
	logSetup.initLogging()

import TextScrape.TextScrapeBase

import readability.readability
import bs4
import webFunctions


class Scrape(TextScrape.TextScrapeBase.TextScraper):
	tableKey = 'prev'
	loggerPath = 'Main.PrRev.Scrape'
	pluginName = 'PRevScrape'

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	threads = 4

	baseUrl = "http://www.princerevolution.org/"
	startUrl = baseUrl

	# Any url containing any of the words in the `badwords` list will be ignored.
	badwords = ["/blog/",
				"/about/credits/",
				"/category/blog/",
				"/recruitment/",
				"wpmp_switcher=mobile",

				# Why do people think they need a fucking comment system?
				'/?replytocom=',

				# Mask out the PDFs
				"-online-pdf-viewer/",

				# Really?
				"/fan-creations/",

				"forums.princerevolution.org",
				"international.princerevolution.org",

				]

	decompose = [
		{'id':'blog-name'},
		{'id': 'sidebar'},
		{'class': 'pagenavi'},
		{'class': 'shailan-dropdown-menu'},
		{'id': 'blog-description'},
		{'id': 'footer'},
		{'id': 'post-meta'},
		{'id': 'fixed-nav'},

		# Facefuck? Really?
		{'id': 'fb-root'},
		# fucking comments
		{'id': 'reaction'},

		# Annoying stick on the homepage.
		{'id': 'post-1191'},

	]


	def extractLinks(self, pageCtnt, url=None):

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
		title = title.replace(" - Baka-Tsuki", "")

		return title, contents




def test():
	scrp = Scrape()
	scrp.crawl()
	# scrp.retreiveItemFromUrl(scrp.startUrl)


if __name__ == "__main__":
	test()




