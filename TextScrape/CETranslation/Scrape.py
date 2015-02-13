
import logSetup
if __name__ == "__main__":
	print("Initializing logging")
	logSetup.initLogging()

import TextScrape.TextScrapeBase

import readability.readability
import bs4
import webFunctions


class Scrape(TextScrape.TextScrapeBase.TextScraper):
	tableKey = 'cetl'
	loggerPath = 'Main.CeTl.Scrape'
	pluginName = 'CETransScrape'

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	threads = 3

	baseUrl = "http://cetranslation.blogspot.com/"
	scannedDomainSet = set(['http://cetranslation.blogspot.com/', 'http://cetranslation.blogspot.sg/'])
	fileDomains = set(['bp.blogspot.com'])
	startUrl = 'http://cetranslation.blogspot.com/p/projects.html'

	# Any url containing any of the words in the `badwords` list will be ignored.
	badwords = [
					'#comment-form',
					'/search/label/',
					'/comments/default',
					'?updated-max=',
					'/subscribe.php',
					'/comments/',
					'.yahoo.com',
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
	allImages = False

	stripTitle = 'C.E. Light Novel Translations:'



def test():
	scrp = Scrape()
	scrp.crawl()
	# scrp.retreiveItemFromUrl(scrp.baseUrl)


if __name__ == "__main__":
	test()




