
import logSetup
if __name__ == "__main__":
	print("Initializing logging")
	logSetup.initLogging()

import TextScrape.TextScrapeBase

import readability.readability
import bs4
import webFunctions


class Scrape(TextScrape.TextScrapeBase.TextScraper):
	tableKey = 'se86'
	loggerPath = 'Main.Se86Tr.Scrape'
	pluginName = 'Setsuna86Scrape'

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	threads = 3

	baseUrl = "https://setsuna86blog.wordpress.com/"

	scannedDomainSet = set(['http://files.wordpress.com', 'https://setsuna86blog.files.wordpress.com'])
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
		{'id'    : 'header'},
		{'class' : 'widget-area'},
		{'id'    : 'primary'},
		{'id'    : 'footer'},
		{'class' : 'bit'},
		{'id'    : 'bit'},
		{'id'    : 'likes-master'},
		{'id'    : 'likes-other-gravatars'},
		{'id'    : 'colophon'},
		{'id'    : 'entry-author-info'},
		{'id'    : 'carousel-reblog-box'},
		{'id'    : 'infinite-footer'},
		{'id'    : 'nav-above'},
		{'id'    : 'jp-post-flair'},
		{'id'    : 'comments'},
		{'class' : 'entry-utility'},

	]



	decomposeBefore = [
		{'class' : 'comments'},
		{'class' : 'comments-area'},
		{'id'    : 'addthis-share'},
		{'id'    : 'info-bt'},
		{'id'    : 'comments'},
	]

	stripTitle = '| SETSUNA86BLOG'




def test():
	scrp = Scrape()
	scrp.crawl()
	# scrp.retreiveItemFromUrl(scrp.startUrl)


if __name__ == "__main__":
	test()




