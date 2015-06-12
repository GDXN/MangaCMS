
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
	tableKey = 'sousetsuka'
	loggerPath = 'Main.Text.Sousetsuka.Scrape'
	pluginName = 'SousetsukaScrape'

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	threads = 1
	FOLLOW_GOOGLE_LINKS = False

	baseUrl = "http://www.sousetsuka.com/"
	startUrl = baseUrl

	feeds = [
		'http://www.sousetsuka.com/feeds/posts/default'
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
				"showComment=",
				"?popup=",
				"viewforum.php",
				"/search?",
				"/feeds/comments/",
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
		{'class' : 'sidebar-wrapper'},
		{'class' : 'disqus_thread'},
		{'class' : 'sharedaddy'},
		{'class' : 'pagination'},
		{'class' : 'scrollUp'},
		{'class' : 'comments'},
		{'class' : 'blog-pager'},
		{'class' : 'menucodenirvana'},

		{'id' : 'navigation'},
		{'id' : 'header'},
		{'id' : 'slider-container'},
		{'id' : 'secondarymenu-container'},
		{'id' : 'mainmenu-container'},
		{'id' : 'mobile-menu'},
		{'id' : 'footer'},
		{'id' : 'sidebar'},
		{'id' : 'addthis-share'},
		{'id' : 'credit'},
		{'id' : 'postFooterGadgets'},
		{'id' : 'comments'},
		{'id' : 'blog-pager'},
		{'id' : 'content-top'},
		{'id' : 'disqus_thread'},
		{'id' : 'sharedaddy'},
		{'id' : 'scrollUp'},
	]

	stripTitle = '| Sousetsuka'






def test():
	scrp = Scrape()
	scrp.crawl()

if __name__ == "__main__":
	test()







