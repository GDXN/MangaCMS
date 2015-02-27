
import logSetup
if __name__ == "__main__":
	print("Initializing logging")
	logSetup.initLogging()

import TextScrape.TextScrapeBase

import readability.readability
import bs4
import webFunctions
import urllib.error

class Scrape(TextScrape.TextScrapeBase.TextScraper):
	tableKey = 'sekaigagame'
	loggerPath = 'Main.SekaiGaGame.Scrape'
	pluginName = 'SekaiGaGameScrape'

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	threads = 1


	baseUrl = "https://sites.google.com/site/sekaigameoredake/"
	startUrl = baseUrl

	badwords = [
				"pages/reportAbuse",

				"fanfic.php",
				"/viewtopic.php",
				"/memberlist.php",
				"/search.php",
				"/wp-content/plugins/",
				"/styles/prosilver/theme/",
				"/forums/",
				"/forum/",
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
	scrp = Scrape()
	scrp.crawl()
	# scrp.retreiveItemFromUrl(scrp.startUrl)
	# new = gdp.GDocExtractor.getDriveFileUrls('https://drive.google.com/folderview?id=0B-x_RxmzDHegRk5iblp4alZmSkU&usp=sharing')


if __name__ == "__main__":
	test()







