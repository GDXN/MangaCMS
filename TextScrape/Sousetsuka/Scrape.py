
import logSetup
if __name__ == "__main__":
	print("Initializing logging")
	logSetup.initLogging()

import TextScrape.TextScrapeBase
import webFunctions


class Scrape(TextScrape.TextScrapeBase.TextScraper):
	tableKey = 'souse'
	loggerPath = 'Main.Sousetsuka.Scrape'
	pluginName = 'SousetsukaScrape'

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	threads = 2

	baseUrl = "https://sousetsuka.blogspot.com/"
	startUrl = baseUrl


	# Any url containing any of the words in the `badwords` list will be ignored.
	badwords = [
				"/manga/",
				"/recruitment/",
				"wpmp_switcher=mobile",
				"account/begin_password_reset",
				"/comment-page-",
				"plus.google.com",

				# Why do people think they need a fucking comment system?
				'/?replytocom=',
				'#comments',

				# Mask out the PDFs
				"-online-pdf-viewer/",
				"like_comment=",
				"_wpnonce=",
				"facebook.com",
				"twitter.com",
				"mailto:",
				"showComment=",
				".yahoo.com",

				# Who the fuck shares shit like this anyways?
				"?share=",

				]


	decomposeBefore = [
		{'class' : 'comments'},
		{'id'    : 'addthis-share'},
		{'id'    : 'info-bt'},
	]

	decompose = [
		{'class' : 'sidebar-wrapper'},
		{'class' : 'menucodenirvana'},
		{'class' : 'comments'},

		{'id'    : 'postFooterGadgets'},
		{'id'    : 'credit'},
		{'id'    : 'addthis-share'},



	]

	stripTitle = '| Sousetsuka'


def test():
	scrp = Scrape()
	scrp.crawl()
	# scrp.retreiveItemFromUrl(scrp.startUrl)


if __name__ == "__main__":
	test()




