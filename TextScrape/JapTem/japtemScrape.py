
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
	startUrl = baseUrl

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

	strip = ['slider-container', 'secondarymenu-container', 'mainmenu-container', 'mobile-menu', 'footer', 'sidebar', 'disqus_thread', 'sharedaddy', 'scrollUp']


	def cleanPage(self, inPage):

		soup = bs4.BeautifulSoup(inPage)
		for rm in self.strip:

			for tag in soup.find_all("div", class_=rm):
				tag.decompose()
			for tag in soup.find_all("select", class_=rm):
				tag.decompose()
			for tag in soup.find_all("div", id=rm):
				tag.decompose()

		inPage = soup.prettify()
		doc = readability.readability.Document(inPage, positive_keywords=self.positive_keywords, negative_keywords=self.negative_keywords)
		doc.parse()
		content = doc.content()

		soup = bs4.BeautifulSoup(content)

		for aTag in soup.find_all("a"):
			try:
				aTag["href"] = self.convertToReaderUrl(aTag["href"])
			except KeyError:
				continue

		for imtag in soup.find_all("img"):
			try:
				imtag["src"] = self.convertToReaderUrl(imtag["src"])
			except KeyError:
				continue


		contents = ''

		for item in soup.body.contents:
			if type(item) is bs4.Tag:
				contents += item.prettify()
			elif type(item) is bs4.NavigableString:
				contents += item
			else:
				print("Wat", item)

		title = doc.title()


		return title, contents




def test():
	scrp = JaptemScrape()
	scrp.crawl()
	# scrp.retreiveItemFromUrl(scrp.startUrl)
	# new = gdp.GDocExtractor.getDriveFileUrls('https://drive.google.com/folderview?id=0B-x_RxmzDHegRk5iblp4alZmSkU&usp=sharing')


if __name__ == "__main__":
	test()







