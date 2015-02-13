
import logSetup
if __name__ == "__main__":
	print("Initializing logging")
	logSetup.initLogging()

import TextScrape.TextScrapeBase

import readability.readability
import bs4
import webFunctions


class Scrape(TextScrape.TextScrapeBase.TextScraper):
	tableKey = 'unf'
	loggerPath = 'Main.Unf.Scrape'
	pluginName = 'UnlimitedNovelFailuresScrape'



	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	threads = 1

	baseUrl = "http://unlimitednovelfailures.mangamatters.com/"

	startUrl = baseUrl

	# Any url containing any of the words in the `badwords` list will be ignored.
	badwords = [
					'/disclaimer/',
					'/about/',
					'like_comment=',
					'replytocom=',
					'?share=',
					'/comment-page-',
					'wp-login.php',
				]

	decompose = [

		{'id'    : 'comment-wrap'},
		{'id'    : 'sidebar'},
		{'id'    : 'content-bottom'},
		{'id'    : 'content-top'},
		{'id'    : 'menu'},
		{'id'    : 'main_bg'},



		{'id'    : "fancybox-tmp"},
		{'id'    : "fancybox-loading"},
		{'id'    : "fancybox-overlay"},
		{'id'    : "fancybox-wrap"},

		{'class' : 'meta-info'},


	]

	stripTitle = '| Unlimited Novel Failures'


def test():
	scrp = Scrape()
	scrp.crawl()
	# scrp.retreiveItemFromUrl(scrp.baseUrl)


if __name__ == "__main__":
	test()




