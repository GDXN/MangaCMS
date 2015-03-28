
import logSetup
if __name__ == "__main__":
	print("Initializing logging")
	logSetup.initLogging()

import TextScrape.SiteArchiver

import readability.readability
import bs4
import webFunctions
import urllib.error

class Scrape(TextScrape.SiteArchiver.SiteArchiver):
	tableKey = 'DearestFairy'
	loggerPath = 'Main.Text.DearestFairy.Scrape'
	pluginName = 'DearestFairyScrape'

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	threads = 1
	FOLLOW_GOOGLE_LINKS = False

	baseUrl = "http://earlandfairy.weebly.com/"
	startUrl = baseUrl

	feeds = [
		'http://guhehe.net/feed/'
	]

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
		{'id'      : 'disqus_thread'},
		{'id'      : 'weebly-footer-signup-container'},
		{'id'      : 'header-top'},
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

		{'id' : 'navigation'},
		{'id' : 'header'},
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

	stripTitle = '- Dearest Fairy'






def test():
	scrp = Scrape()
	scrp.crawl()

if __name__ == "__main__":
	test()







