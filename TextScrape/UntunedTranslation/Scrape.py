
import logSetup
if __name__ == "__main__":
	print("Initializing logging")
	logSetup.initLogging()

import TextScrape.TextScrapeBase

import readability.readability
import bs4
import webFunctions


class Scrape(TextScrape.TextScrapeBase.TextScraper):
	tableKey = 'untl'
	loggerPath = 'Main.UnTl.Scrape'
	pluginName = 'UntunedTransScrape'

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	threads = 3

	baseUrl = "http://untuned-strings.blogspot.com/"
	fileDomains = set(['bp.blogspot.com'])
	startUrl = baseUrl

	# Any url containing any of the words in the `badwords` list will be ignored.
	badwords = [
					'#comment-form',
					'/search/label/',
					'/search?',
					'/comments/default',
				]

	decompose = [
		{'id'    : 'header'},

		{'class'  : 'column-right-outer'},
		{'class'  : 'column-left-outer'},
		{'class'  : 'tabs-outer'},
		{'class'  : 'header-outer'},
		{'class'  : 'menujohanes'},
		{'class'  : 'date-header'},
		{'class'  : 'comments'},
		{'class'  : 'komensamping'},
		{'class'  : 'navbar'},
		{'class'  : 'footer'},
		{'class'  : 'blog-pager'},
		{'class'  : 'post-feeds'},
		{'class'  : 'post-footer'},
		{'class'  : 'post-feeds'},
		{'class'  : 'blog-feeds'},
		{'class'  : 'footer-outer'},
		{'class'  : 'quickedit'},
		{'class'  : 'widget-content'},
		{'id'  : 'sidebar-wrapper1'}, # Yes, two `sidebar-wrapper` ids. Gah.
		{'id'  : 'sidebar-wrapper'},
		{'class'  : 'btop'},
		{'class'  : 'headerbg'},
		{'id'  : 'credit-wrapper'},
		{'class'  : 'sidebar'},
		{'class'  : 'authorpost'},




	]

	# Grab all images, ignoring host domain
	allImages = True

	stripTitle = "Untuned Translation Blog:"

def test():
	scrp = Scrape()
	scrp.crawl()
	# scrp.retreiveItemFromUrl(scrp.baseUrl)


if __name__ == "__main__":
	test()




