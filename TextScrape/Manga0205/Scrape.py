
import logSetup
if __name__ == "__main__":
	print("Initializing logging")
	logSetup.initLogging()

import TextScrape.TextScrapeBase
import webFunctions


class Scrape(TextScrape.TextScrapeBase.TextScraper):
	tableKey = 'm0205'
	loggerPath = 'Main.Manga0205.Scrape'
	pluginName = 'Manga0205Scrape'

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	threads = 1

	baseUrl = "https://Manga0205.wordpress.com/"
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
				"like_comment=",
				"_wpnonce=",

				# Who the fuck shares shit like this anyways?
				"?share=",

				]


	decomposeBefore = [
		{'id'         : 'comments'},
	]

	decompose = [
		{'class' : 'site-header'},
		{'id'    : 'site-header'},
		{'id'    : 'secondary'},
		{'class' : 'header-main'},
		{'class' : 'widget-area'},
		{'id'    : 'jp-post-flair'},
		{'class' : 'entry-meta'},
		{'class' : 'post-navigation'},
		{'class' : 'navigation'},
		{'id'    : 'comments'},
		{'class' : 'site-info'},



		{'id'    : 'footer'},
		{'class' : 'site-footer'},
		{'class' : 'photo-meta'},
		{'class' : 'menu-toggle'},
		{'class' : 'navigation-main'},
		{'class' : 'wpcnt'},
		{'class' : 'bit'},
		{'id'    : 'bit'},
		{'id'    : 'search-container'},
		{'id'    : 'likes-other-gravatars'},
		{'id'    : 'sidebar'},
		{'id'    : 'carousel-reblog-box'},
		{'id'    : 'infinite-footer'},
		{'id'    : 'nav-above'},
		{'id'    : 'nav-below'},
		{'class' : 'entry-utility'},
		{'name'  : 'likes-master'},

	]

	stripTitle = '| manga0205'


def test():
	scrp = Scrape()
	scrp.crawl()
	# scrp.retreiveItemFromUrl(scrp.startUrl)


if __name__ == "__main__":
	test()




