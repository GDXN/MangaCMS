
import logSetup
if __name__ == "__main__":
	print("Initializing logging")
	logSetup.initLogging()

import TextScrape.TextScrapeBase

import webFunctions

class Scrape(TextScrape.TextScrapeBase.TextScraper):
	'''
	This appears to be hosted by the same people as FictionPress.
	The website sure looks to be the same codebase, in any event.
	'''


	tableKey = 'fanfiction'
	loggerPath = 'Main.FanFiction.Scrape'
	pluginName = 'FanFictionScrape'

	tableName       = "book_western_items"
	changeTableName = "book_western_changes"

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	threads = 5

	FOLLOW_GOOGLE_LINKS = False
	allImages = False


	baseUrl = [
		"https://www.fanfiction.net/",
		]
	startUrl = baseUrl

	badwords = [
				"/about/",
				"/join-us/",
				"/chat/",
				'&format=pdf',
				'?format=pdf',
				'?replytocom=',
				"/forum/",
				"/forum",
				"/forums/",
				"/forums",
				"/games/",
				"/betareaders/",
				"/poetry/", # Really?

				"/post.php?",
				"/author.php?",
				]

	# Content Stripping needs to be determined.
	decomposeBefore = [

	]

	decompose = [

	]

	stripTitle = '| FanFiction'




def test():
	scrp = Scrape()
	scrp.crawl()
	# scrp.retreiveItemFromUrl(scrp.startUrl)
	# new = gdp.GDocExtractor.getDriveFileUrls('https://drive.google.com/folderview?id=0B-x_RxmzDHegRk5iblp4alZmSkU&usp=sharing')


if __name__ == "__main__":
	test()

