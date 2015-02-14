
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
		{'class' : 'wpcnt'},

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
		'http://www.maoyuuthetranslation.wordpress.com/',
		'http://www.mayochikithetranslation.wordpress.com',
		'http://www.ojamajothetranslation.wordpress.com',
		'http://www.oregairuthetranslation.wordpress.com',
		'http://www.oreimothetranslation.wordpress.com',
		'http://www.rokkathetranslation.wordpress.com/',
		'http://www.sasamisanthetranslation.wordpress.com',
		'http://www.seizonthetranslation.wordpress.com',
		'http://www.skyworldthetranslation.wordpress.com',


		'http://amaburithetranslation.wordpress.com',
		'http://fateapocryphathetranslation.wordpress.com',
		'http://fuyuugakuenthetranslation.wordpress.com',
		'http://gjbuthetranslation.wordpress.com',
		'http://grimgalthetranslation.wordpress.com',
		'http://hennekothetranslation.wordpress.com',
		'http://korezombiethetranslation.wordpress.com',
		'http://loveyouthetranslation.wordpress.com',
		'http://maoyuuthetranslation.wordpress.com/',
		'http://mayochikithetranslation.wordpress.com',
		'http://ojamajothetranslation.wordpress.com',
		'http://oregairuthetranslation.wordpress.com',
		'http://oreimothetranslation.wordpress.com',
		'http://rokkathetranslation.wordpress.com/',
		'http://sasamisanthetranslation.wordpress.com',
		'http://seizonthetranslation.wordpress.com',
		'http://skyworldthetranslation.wordpress.com',
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

	stripTitle = '| なのですよ！'



def test():
	scrp = Scrape()
	scrp.crawl()
	# scrp.retreiveItemFromUrl(scrp.startUrl)


if __name__ == "__main__":
	test()




