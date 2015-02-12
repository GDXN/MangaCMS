
import logSetup
if __name__ == "__main__":
	print("Initializing logging")
	logSetup.initLogging()

import TextScrape.TextScrapeBase

import readability.readability
import bs4
import webFunctions


class TsukiScrape(TextScrape.TextScrapeBase.TextScraper):
	tableKey = 'tsuki'
	loggerPath = 'Main.Tsuki.Scrape'
	pluginName = 'TsukiScrape'

	wg = webFunctions.WebGetRobust(logPath=loggerPath+".Web")

	threads = 4


	baseUrl = "http://www.baka-tsuki.org/"
	startUrl = baseUrl

	badwords = ["/blog/",
				"/forums/",

				# Yes, I only speak&read english. Leave me to my filtering shame.
				"Category:German",
				"Category:Spanish",
				"Category:French",
				"Category:Vietnamese",
				"Category:Russian",
				"Category:Brazilian_Portuguese",
				"Category:Italian",
				"Category:Polish",
				"Category:Romanian",
				"Category:Hungarian",
				"Category:Norwegian",
				"Category:Korean",
				"Category:Lithuanian",
				"Category:Indonesian",
				"Category:Greek",
				"Category:Turkish",
				"Category:Filipino",
				"Category:Czech",
				"Category:Esperanto",

				# Block user pages
				"title=User:",
				"=Talk:",
				"=talk:",

				# Links within page
				"http://www.baka-tsuki.org/#",

				# misc
				"viewforum.php",
				"viewtopic.php",
				"memberlist.php",
				"printable=yes",
				"/forums/",
				"title=Special",
				"action=edit",
				"action=history",
				"action=info",
				"title=Help:",
				"?title=User_talk:",
				"&oldid=",
				"title=Baka-Tsuki:",
				"title=Special:Book"]



	def changeFilter(self, url, title, changePercentage):
		# Skip title cruft on baka-tsuki
		if title.strip().startswith("File:"):
			return True

		if title.strip().startswith("Information for"):
			return True

		return False

	def extractLinks(self, pageCtnt, url=None):
		doc = readability.readability.Document(inPage, negative_keywords=['mw-normal-catlinks', "printfooter", "mw-panel", 'portal'])
		doc.parse()
		content = doc.content()
		soup = bs4.BeautifulSoup(content)

		# Permute page tree, extract (and therefore remove) all nav tags.
		for tag in soup.find_all(role="navigation"):
			tag.decompose()
		contents = ''


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




		for item in soup.body.contents:
			if type(item) is bs4.Tag:
				contents += item.prettify()
			elif type(item) is bs4.NavigableString:
				contents += item
			else:
				print("Wat", item)

		title = doc.title()
		title = title.replace(" - Baka-Tsuki", "")

		return title, contents


def test():
	scrp = TsukiScrape()
	scrp.crawl()
	# scrp.retreiveItemFromUrl(scrp.startUrl)
	# new = gdp.GDocExtractor.getDriveFileUrls('https://drive.google.com/folderview?id=0B-x_RxmzDHegRk5iblp4alZmSkU&usp=sharing')


if __name__ == "__main__":
	test()




