
import logSetup
if __name__ == "__main__":
	print("Initializing logging")
	logSetup.initLogging()

import TextScrape.TextScrapeBase

import readability.readability
import bs4
import webFunctions


class Scrape(TextScrape.TextScrapeBase.TextScraper):
	tableKey = 'ntl'
	loggerPath = 'Main.NanoDesuTr.Scrape'
	pluginName = 'NanoDesuScrape'

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	threads = 4

	baseUrl = "https://nanodesutranslations.wordpress.com/"
	startUrl = 'https://nanodesutranslations.wordpress.com/translation-projects/project_list/'

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


	scannedDomains = set((
		'http://www.amaburithetranslation.wordpress.com',
		'http://www.fateapocryphathetranslation.wordpress.com',
		'http://www.fuyuugakuenthetranslation.wordpress.com',
		'http://www.gjbuthetranslation.wordpress.com',
		'http://www.grimgalthetranslation.wordpress.com',
		'http://www.hennekothetranslation.wordpress.com',
		'http://www.korezombiethetranslation.wordpress.com',
		'http://www.loveyouthetranslation.wordpress.com',
		'http://maoyuuthetranslation.wordpress.com/',
		'http://www.mayochikithetranslation.wordpress.com',
		'http://www.ojamajothetranslation.wordpress.com',
		'http://www.oregairuthetranslation.wordpress.com',
		'http://www.oreimothetranslation.wordpress.com',
		'http://rokkathetranslation.wordpress.com/',
		'http://www.sasamisanthetranslation.wordpress.com',
		'http://www.seizonthetranslation.wordpress.com',
		'http://www.skyworldthetranslation.wordpress.com',
	))

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
		title = title.replace(" | なのですよ！", "")

		return title, contents


def test():
	scrp = Scrape()
	scrp.crawl()
	# scrp.retreiveItemFromUrl(scrp.startUrl)


if __name__ == "__main__":
	test()




