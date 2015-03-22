
import logSetup
if __name__ == "__main__":
	print("Initializing logging")
	logSetup.initLogging()

from TextScrape.SiteArchiver import SiteArchiver

import readability.readability
import bs4
import webFunctions
import urllib.error

class Scrape(SiteArchiver):
	tableKey = 'guhehe'
	loggerPath = 'Main.Guhehe.Scrape'
	pluginName = 'GuheheScrape'

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	threads = 3


	baseUrl = [
		"http://guhehe.net/",
		"http://www.guhehe.net/"
		]
	startUrl = 'http://guhehe.net/volumes/'

	badwords = [
				"/about/",
				"/join-us/",
				"/chat/",
				'&format=pdf',
				'?format=pdf',
				'?replytocom=',
				]

	# positive_keywords = ['main_content']

	# negative_keywords = ['mw-normal-catlinks',
	# 					"printfooter",
	# 					"mw-panel",
	# 					'portal']


	decomposeBefore = [
		{'class'      :'comments-area'},
	]

	decompose = [


		{'class'  : 'main-nav'},
		{'class'  : 'inside-right-sidebar'},
		{'class'  : 'screen-reader-text'},
		{'class'  : 'site-footer'},
		{'class'  : 'menu-toggle'},
		{'class'  : 'site-header'},
		{'class'  : 'paging-navigation'},
		{'class'  : 'comments-area'},
	]

	stripTitle = 'guhehe.TRANSLATIONS |'




def test():
	scrp = GuheheScrape()
	scrp.crawl()
	# scrp.retreiveItemFromUrl(scrp.startUrl)
	# new = gdp.GDocExtractor.getDriveFileUrls('https://drive.google.com/folderview?id=0B-x_RxmzDHegRk5iblp4alZmSkU&usp=sharing')


if __name__ == "__main__":
	test()

