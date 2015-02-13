
import logSetup
if __name__ == "__main__":
	print("Initializing logging")
	logSetup.initLogging()

import TextScrape.TextScrapeBase

import readability.readability
import bs4
import webFunctions
import urllib.error

class GuheheScrape(TextScrape.TextScrapeBase.TextScraper):
	tableKey = 'guhehe'
	loggerPath = 'Main.Guhehe.Scrape'
	pluginName = 'GuheheScrape'

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	threads = 2


	baseUrl = "http://guhehe.net/"
	startUrl = 'http://guhehe.net/series/'

	badwords = [
				"/about/",
				"/join-us/",
				"/chat/",
				'&format=pdf',
				'?format=pdf',
				'?replytocom=',
				]

	positive_keywords = ['main_content']

	negative_keywords = ['mw-normal-catlinks',
						"printfooter",
						"mw-panel",
						'portal']


	decompose = [
				{'id':'main-header'},
				{'id':'main-footer'},
				{'id':'comment-wrap'},
				{'id':'sidebar'},
				]

	stripTitle = '| guhehe.TRANSLATIONS'




def test():
	scrp = GuheheScrape()
	scrp.crawl()
	# scrp.retreiveItemFromUrl(scrp.startUrl)
	# new = gdp.GDocExtractor.getDriveFileUrls('https://drive.google.com/folderview?id=0B-x_RxmzDHegRk5iblp4alZmSkU&usp=sharing')


if __name__ == "__main__":
	test()

