
import logSetup
if __name__ == "__main__":
	print("Initializing logging")
	logSetup.initLogging()

import TextScrape.TextScrapeBase

import readability.readability
import bs4
import webFunctions


class Scrape(TextScrape.TextScrapeBase.TextScraper):
	tableKey = 'sktl'
	loggerPath = 'Main.SakuraHonyakuTr.Scrape'
	pluginName = 'SakuraHonyakuScrape'

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	threads = 3

	baseUrl = "https://sakurahonyaku.wordpress.com/"
	startUrl = 'https://sakurahonyaku.wordpress.com/projects/'

	fileDomains = set(['files.wordpress.com'])

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
		{'id'    : 'bit'},
		{'id'    :'header-meta'},
		{'class' : 'widget-area'},
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
		{'id'    : 'comments'},
		{'class' : 'entry-utility'},
		{'class' : 'entry-meta'},
		{'class' : 'wpa'},   # Ads, I think.

	]


	stripTitle = '| 桜翻訳!'




def test():
	scrp = Scrape()
	scrp.crawl()
	# scrp.retreiveItemFromUrl(scrp.startUrl)


if __name__ == "__main__":
	test()




