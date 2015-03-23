
import logSetup
if __name__ == "__main__":
	print("Initializing logging")
	logSetup.initLogging()

from TextScrape.SiteArchiver import SiteArchiver

import webFunctions

class Scrape(SiteArchiver):
	tableKey = 'fictionpress'
	loggerPath = 'Main.Text.FictionPress.Scrape'
	pluginName = 'FictionPressScrape'

	tableName       = "book_western_items"
	changeTableName = "book_western_changes"

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	threads = 5

	FOLLOW_GOOGLE_LINKS = False
	allImages = False


	baseUrl = [
		"https://www.fictionpress.com/",
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

	stripTitle = ''




def test():
	scrp = Scrape()
	scrp.crawl()
	# scrp.retreiveItemFromUrl(scrp.startUrl)
	# new = gdp.GDocExtractor.getDriveFileUrls('https://drive.google.com/folderview?id=0B-x_RxmzDHegRk5iblp4alZmSkU&usp=sharing')


if __name__ == "__main__":
	test()

