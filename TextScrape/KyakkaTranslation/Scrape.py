
import logSetup
if __name__ == "__main__":
	print("Initializing logging")
	logSetup.initLogging()

import TextScrape.TextScrapeBase

import readability.readability
import bs4
import webFunctions


class Scrape(TextScrape.TextScrapeBase.TextScraper):
	tableKey = 'kytl'
	loggerPath = 'Main.KyakkaTr.Scrape'
	pluginName = 'KyakkaScrape'

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	threads = 2

	baseUrl = "https://kyakka.wordpress.com/"
	scannedDomainSet = set(['https://kyakka.wordpress.com', 'https://kyakka.files.wordpress.com'])
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
				'/feed/',

				# Mask out the PDFs
				"-online-pdf-viewer/",

				# Who the fuck shares shit like this anyways?
				"?share=",

				]

	decompose = [
		{'id'    : 'secondary'},
		{'id'    : 'branding'},
		{'class' : 'bit'},
		{'class' : 'wpcnt'},
		{'id'    : 'bit'},
		{'id'    : 'header-meta'},
		{'id'    : 'header'},
		{'class' : 'widget-area'},
		{'class' : 'comments-link'},
		{'name'  : 'likes-master'},


		{'id'    : 'footer'},
		{'id'    : 'colophon'},
		{'id'    : 'access'},
		{'class' : 'photo-meta'},
		{'id'    : 'likes-other-gravatars'},
		{'id'    : 'sidebar'},
		{'id'    : 'carousel-reblog-box'},
		{'id'    : 'infinite-footer'},
		{'id'    : 'nav-above'},
		{'id'    : 'nav-below'},
		{'id'    : 'jp-post-flair'},
		{'id'    : 'respond'},
		{'id'    : 'comments'},
		{'class' : 'commentlist'},
		{'class' : 'entry-utility'},
		{'class' : 'entry-meta'},
		{'class' : 'wpa'},   # Ads, I think.

	]



	decomposeBefore = [
		{'class' : 'comments'},
		{'class' : 'comments-area'},
		{'id'    : 'addthis-share'},
		{'id'    : 'info-bt'},
	]

	stripTitle = '| Kyakka'


def test():
	scrp = Scrape()
	scrp.crawl()
	# scrp.retreiveItemFromUrl(scrp.startUrl)


if __name__ == "__main__":
	test()




