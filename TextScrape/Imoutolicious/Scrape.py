
import logSetup
if __name__ == "__main__":
	print("Initializing logging")
	logSetup.initLogging()

import TextScrape.TextScrapeBase

import readability.readability
import bs4
import webFunctions


class Scrape(TextScrape.TextScrapeBase.TextScraper):
	tableKey = 'iml'
	loggerPath = 'Main.Iml.Scrape'
	pluginName = 'ImoutoliciousScrape'

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	threads = 3

	baseUrl = "http://imoutoliciouslnt.blogspot.ca/"
	fileDomains = set(['bp.blogspot.com'])
	startUrl = 'http://imoutoliciouslnt.blogspot.ca/p/projects.html'

	# Any url containing any of the words in the `badwords` list will be ignored.
	badwords = [
					'#comment-form',
					'the-imouto-petter.html',
					'/search/label/',
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

	stripTitle = 'Imoutolicious Light Novel Translations:'

def test():
	scrp = Scrape()
	scrp.crawl()
	# scrp.retreiveItemFromUrl(scrp.baseUrl)


if __name__ == "__main__":
	test()




