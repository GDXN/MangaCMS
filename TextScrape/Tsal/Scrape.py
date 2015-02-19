
import logSetup
if __name__ == "__main__":
	print("Initializing logging")
	logSetup.initLogging()

import TextScrape.WordpressScrape

import webFunctions


class Scrape(TextScrape.WordpressScrape.WordpressScrape):
	tableKey = 'tsal'
	loggerPath = 'Main.Tsal.Scrape'
	pluginName = 'TsalScrape'

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	threads = 1

	baseUrl = "http://tsaltranslations.wordpress.com/"
	startUrl = baseUrl


	scannedDomains = set((
		'http://tsaltranslation.wordpress.com/',
	))

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

		{'id'    : 'footer'},
		{'class' : 'photo-meta'},
		{'class' : 'bit'},
		{'id'    : 'bit'},
		{'id'    : 'headerimg'},
		{'id'    : 'likes-other-gravatars'},
		{'id'    : 'sidebar'},
		{'id'    : 'carousel-reblog-box'},
		{'id'    : 'infinite-footer'},
		{'id'    : 'nav-above'},
		{'id'    : 'nav-below'},
		{'id'    : 'jp-post-flair'},
		{'id'    : 'comments'},
		{'class' : 'entry-utility'},
		{'class' : 'widget-container'},
		{'class' : 'wpcom-follow-bubbles'},
		{'class' : 'wpcnt'},
		{'id'    : 'site-navigation'},

	]

	decomposeBefore = [
		{'class' : 'comments'},
		{'class' : 'wpcnt'},
		{'id'    : 'comments'},
		{'class' : 'comments-area'},
		{'id'    : 'addthis-share'},
		{'id'    : 'info-bt'},
		{'id'    : 'jp-post-flair'},
	]

	stripTitle = "| Light Novel translations"



def test():
	scrp = Scrape()
	scrp.crawl()
	# scrp.retreiveItemFromUrl(scrp.startUrl)


if __name__ == "__main__":
	test()




