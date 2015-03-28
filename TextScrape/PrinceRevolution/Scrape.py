
import logSetup
if __name__ == "__main__":
	print("Initializing logging")
	logSetup.initLogging()

import TextScrape.SiteArchiver

import readability.readability
import bs4
import webFunctions


class Scrape(TextScrape.SiteArchiver.SiteArchiver):
	tableKey = 'prev'
	loggerPath = 'Main.Text.PrRev.Scrape'
	pluginName = 'PRevScrape'

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	threads = 4

	baseUrl = "http://www.princerevolution.org/"
	startUrl = baseUrl


	feeds = [
		'http://www.princerevolution.org/feed/'
	]


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
		{'id'    :'blog-name'},
		{'id'    : 'sidebar'},
		{'class' : 'pagenavi'},
		{'class' : 'shailan-dropdown-menu'},
		{'id'    : 'blog-description'},
		{'id'    : 'footer'},
		{'id'    : 'post-meta'},
		{'id'    : 'fixed-nav'},

		# Facefuck? Really?
		{'id'    : 'fb-root'},
		# fucking comments
		{'id'    : 'reaction'},

		# Annoying stick on the homepage.
		{'id'    : 'post-1191'},


		{'id'    : 'header'},
		{'class' : 'widget-area'},
		{'id'    : 'primary'},
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
		{'id'    : 'reaction'},
	]



def test():
	scrp = Scrape()
	scrp.crawl()
	# scrp.retreiveItemFromUrl(scrp.startUrl)


if __name__ == "__main__":
	test()




