
import logSetup
if __name__ == "__main__":
	print("Initializing logging")
	logSetup.initLogging()

import TextScrape.TextScrapeBase

import webFunctions
import http.cookiejar
import urllib.parse

class Scrape(TextScrape.TextScrapeBase.TextScraper):
	tableKey = 'storiesonline'
	loggerPath = 'Main.StoriesOnline.Scrape'
	pluginName = 'StoriesOnlineScrape'

	tableName       = "book_western_items"
	changeTableName = "book_western_changes"

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	threads = 8

	FOLLOW_GOOGLE_LINKS = False
	allImages = False


	baseUrl = [
		"http://storiesonline.net/",

		]
	startUrl = 'http://storiesonline.net/home.php'

	badwords = [
				"/about/",
				"/join-us/",
				"/chat/",
				'&format=pdf',
				'/adpeeps/',
				'/ads/',
				'/java/'
				'/globals/',
				'adpeeps.php',
				'?format=pdf',
				'?replytocom=',
				"/forum/",
				"/forum",
				"/forums/",
				"/forums",
				"/games/",
				"/betareaders/",
				"/poetry/", # Really?

				"/MyAccount/",

				"/login.php"

				"/post.php?",
				"/author.php?",
				"big.oscar.aol.com",

				'ne.adult-fanfiction.org',   # Non-english

				'review.php?', # Filter reviews (possibly should be revisited?)
				]

	# Content Stripping needs to be determined.
	decomposeBefore = [

	]

	decompose = [

	]

	stripTitle = ''

	# Kind of vaugely worth implementing login support? StoriesOnline is kind of a dick about registration bullshit and has access limits, though.

	# def preFlight(self):
	# 	self.spoofCookies()
	# 	self.spoofVerifier()



def test():
	scrp = Scrape()
	scrp.crawl()
	# scrp.retreiveItemFromUrl(scrp.startUrl)
	# new = gdp.GDocExtractor.getDriveFileUrls('https://drive.google.com/folderview?id=0B-x_RxmzDHegRk5iblp4alZmSkU&usp=sharing')


if __name__ == "__main__":
	test()

