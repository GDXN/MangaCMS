
import logSetup
if __name__ == "__main__":
	print("Initializing logging")
	logSetup.initLogging()

import TextScrape.TextScrapeBase

import readability.readability
import bs4
import webFunctions
import urllib.error

class JaptemScrape(TextScrape.TextScrapeBase.TextScraper):
	tableKey = 'japtem'
	loggerPath = 'Main.JapTem.Scrape'
	pluginName = 'JapTemScrape'

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	threads = 2


	baseUrl = "http://japtem.com/"
	startUrl = 'http://japtem.com/ul-volume-5-chapter-7/'

	badwords = ["fanfic.php",
				"/forums/",
				"/fanfic",         # Fucking slash fics.
				"/cdn-cgi/",
				"/help/",
				"?share=",
				"?popup=",
				"viewforum.php",
				"/wp-login.php",
				"/#comments",      # Ignore in-page anchor tags
				"/staff/"]

	positive_keywords = ['main_content']

	negative_keywords = ['mw-normal-catlinks',
						"printfooter",
						"mw-panel",
						'portal']




	decomposeBefore = [
		{'id'      :'disqus_thread'},
	]


	decompose = [
		{'class' : 'slider-container'},
		{'class' : 'secondarymenu-container'},
		{'class' : 'mainmenu-container'},
		{'class' : 'mobile-menu'},
		{'class' : 'footer'},
		{'class' : 'sidebar'},
		{'class' : 'disqus_thread'},
		{'class' : 'sharedaddy'},
		{'class' : 'pagination'},
		{'class' : 'scrollUp'},

		{'id' : 'slider-container'},
		{'id' : 'secondarymenu-container'},
		{'id' : 'mainmenu-container'},
		{'id' : 'mobile-menu'},
		{'id' : 'footer'},
		{'id' : 'sidebar'},
		{'id' : 'disqus_thread'},
		{'id' : 'sharedaddy'},
		{'id' : 'scrollUp'},
	]





def test():
	scrp = JaptemScrape()
	scrp.crawl()
	# scrp.retreiveItemFromUrl(scrp.startUrl)
	# new = gdp.GDocExtractor.getDriveFileUrls('https://drive.google.com/folderview?id=0B-x_RxmzDHegRk5iblp4alZmSkU&usp=sharing')


if __name__ == "__main__":
	test()







