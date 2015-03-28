
import logSetup
if __name__ == "__main__":
	print("Initializing logging")
	logSetup.initLogging()

import TextScrape.SiteArchiver

import readability.readability
import bs4
import webFunctions


class Scrape(TextScrape.SiteArchiver.SiteArchiver):
	tableKey = 'kryt'
	loggerPath = 'Main.Text.Kry.Scrape'
	pluginName = 'KrytykScrape'

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	threads = 4

	baseUrl = "http://krytykal.org/"
	startUrl = baseUrl

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
		{'class' : 'nav-menu'},
		{'id'    : 'site-navigation'},
		{'id'    : 'masthead'},
		{'id'    : 'footer'},
		{'class' : 'bit'},
		{'class' : 'comments-link'},
		{'id'    : 'nav-above'},
		{'id'    : 'nav-below'},
		{'id'    : 'colophon'},

		{'id'    : 'jp-post-flair'},
		{'id'    : 'comments'},
		{'class' : 'entry-utility'},

	]

	decomposeBefore = [
		{'class' : 'comments'},
		{'class' : 'comments-area'},
		{'id'    : 'addthis-share'},
		{'id'    : 'info-bt'},
	]

	stripTitle = "| Krytyk's translations"


def test():
	scrp = Scrape()
	scrp.crawl()
	# scrp.retreiveItemFromUrl(scrp.baseUrl)


if __name__ == "__main__":
	test()




