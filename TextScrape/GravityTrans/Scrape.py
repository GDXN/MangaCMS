
import logSetup
if __name__ == "__main__":
	print("Initializing logging")
	logSetup.initLogging()

import TextScrape.TextScrapeBase

import webFunctions


class Scrape(TextScrape.TextScrapeBase.TextScraper):
	tableKey = 'gravtl'
	loggerPath = 'Main.GravityTr.Scrape'
	pluginName = 'GravityScrape'

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	threads = 4

	baseUrl = "http://gravitytranslations.wordpress.com/"
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
				'pixel.wp.com',
				# Mask out the PDFs
				"-online-pdf-viewer/",

				# Who the fuck shares shit like this anyways?
				"?share=",

				]

	decompose = [
		{'id'    :'header'},
		{'class' : 'widget-area'},

		{'id'    : 'footer'},
		{'class' : 'photo-meta'},
		{'class' : 'site-header'},
		{'class' : 'site-footer'},
		{'class' : 'entry-meta'},
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
		{'class' : 'wpcnt'},
		{'class' : 'menu-toggle'},
		{'class' : 'screen-reader-text'},
		{'class' : 'navigation-main'},
		{'name'  : 'likes-master'},
		{'ic'    : 'likes-master'},


	]


	scannedDomains = set((
		'http://www.hellotranslations.wordpress.com',
		'http://hellotranslations.wordpress.com',
		'http://www.gravitytranslations.wordpress.com/',


		'http://files.wordpress.com',
		'http://gravitytranslations.files.wordpress.com'
		'http://hellotranslations.files.wordpress.com'
		'http://www.gravitytranslations.files.wordpress.com'
		'http://www.hellotranslations.files.wordpress.com'


	))



	decomposeBefore = [
		{'class' : 'comments'},
		{'class' : 'wpcnt'},
		{'id'    : 'comments'},
		{'class' : 'comments-area'},
		{'id'    : 'addthis-share'},
		{'id'    : 'info-bt'},
		{'id'    : 'jp-post-flair'},
	]

	stripTitle = '| Gravity translation'



def test():
	scrp = Scrape()
	scrp.crawl()
	# scrp.retreiveItemFromUrl(scrp.startUrl)


if __name__ == "__main__":
	test()




