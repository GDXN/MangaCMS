
import logSetup
if __name__ == "__main__":
	print("Initializing logging")
	logSetup.initLogging()

import TextScrape.TextScrapeBase

import readability.readability
import bs4
import webFunctions


class Scrape(TextScrape.TextScrapeBase.TextScraper):
	tableKey = 'stw'
	loggerPath = 'Main.Stw.Scrape'
	pluginName = 'SkyTheWoodScrape'

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	threads = 3

	baseUrl = "http://skythewood.blogspot.sg/"

	scannedDomainSet = set(['http://skythewood.blogspot.sg/', 'http://skythewood.blogspot.com/'])
	fileDomains = set(['bp.blogspot.com'])
	startUrl = baseUrl

	# Any url containing any of the words in the `badwords` list will be ignored.
	badwords = [
					'#comment-form',
					'/search/label/',
					'/search?',
					'/feeds/',
				]


	decomposeBefore = [
		{'class'      :'post-share-buttons'},
		{'class'      :'comments'},
	]

	decompose = [
		{'id'    : 'header'},

		{'class'  : 'column-right-outer'},
		{'class'  : 'column-left-outer'},
		{'class'  : 'tabs-outer'},
		{'class'  : 'header-outer'},
		{'class'  : 'date-header'},
		{'class'  : 'comments'},
		{'class'  : 'blog-pager'},
		{'class'  : 'post-feeds'},
		{'class'  : 'post-footer'},
		{'class'  : 'post-feeds'},
		{'class'  : 'blog-feeds'},
		{'class'  : 'footer-outer'},
		{'class'  : 'quickedit'},
		{'class'  : 'widget-content'},


	]

	# Grab all images, ignoring host domain
	allImages = True

	stripTitle = 'Skythewood translations:'



def test():
	scrp = Scrape()
	scrp.crawl()
	# scrp.retreiveItemFromUrl(scrp.baseUrl)


if __name__ == "__main__":
	test()




